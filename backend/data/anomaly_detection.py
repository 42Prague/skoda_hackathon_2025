"""
Ingestion Anomaly Detection
Detects data quality issues during upload:
- Volume spikes (sudden increase in row count)
- Date drift (timestamps too old or in future)
- Malformed headers (missing/wrong columns)
- Data type violations
"""
import os
import psycopg2
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd


def get_db_connection():
    """Get PostgreSQL connection from environment"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please configure DATABASE_URL with your PostgreSQL connection string."
        )
    return psycopg2.connect(database_url)


class IngestionAnomalyDetector:
    """
    Detects data quality anomalies during file ingestion
    """

    def __init__(self):
        self.anomalies = []
        self.warnings = []

    def detect_volume_spike(
        self,
        current_row_count: int,
        source: str,
        spike_threshold: float = 3.0
    ) -> Dict[str, Any]:
        """
        Detect volume spike by comparing to historical averages

        Args:
            current_row_count: Number of rows in current upload
            source: Data source identifier (e.g., 'HR_SYSTEM', 'LMS')
            spike_threshold: Multiplier for spike detection (default: 3x average)

        Returns:
            {
                'is_anomaly': bool,
                'severity': 'critical' | 'warning' | 'normal',
                'message': str,
                'current_volume': int,
                'avg_volume': float,
                'spike_ratio': float
            }
        """
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Get historical average row count for this source (last 30 days)
            cur.execute("""
                SELECT AVG(rows_processed)::int as avg_rows
                FROM upload_history
                WHERE format_detected = %s
                  AND upload_date > NOW() - INTERVAL '30 days'
                  AND status = 'success'
            """, (source,))

            result = cur.fetchone()
            avg_rows = result[0] if result and result[0] else None

            if avg_rows is None or avg_rows == 0:
                # No historical data - can't detect spike
                return {
                    'is_anomaly': False,
                    'severity': 'normal',
                    'message': 'No historical baseline (first upload or no successful uploads in 30 days)',
                    'current_volume': current_row_count,
                    'avg_volume': None,
                    'spike_ratio': None
                }

            spike_ratio = current_row_count / avg_rows

            if spike_ratio > spike_threshold:
                severity = 'critical' if spike_ratio > spike_threshold * 2 else 'warning'
                return {
                    'is_anomaly': True,
                    'severity': severity,
                    'message': f'Volume spike detected: {current_row_count} rows vs {avg_rows} avg ({spike_ratio:.1f}x increase)',
                    'current_volume': current_row_count,
                    'avg_volume': avg_rows,
                    'spike_ratio': round(spike_ratio, 2)
                }

            elif spike_ratio < (1.0 / spike_threshold):
                # Volume drop
                return {
                    'is_anomaly': True,
                    'severity': 'warning',
                    'message': f'Volume drop detected: {current_row_count} rows vs {avg_rows} avg ({spike_ratio:.1f}x decrease)',
                    'current_volume': current_row_count,
                    'avg_volume': avg_rows,
                    'spike_ratio': round(spike_ratio, 2)
                }

            else:
                return {
                    'is_anomaly': False,
                    'severity': 'normal',
                    'message': 'Volume within normal range',
                    'current_volume': current_row_count,
                    'avg_volume': avg_rows,
                    'spike_ratio': round(spike_ratio, 2)
                }

        finally:
            cur.close()
            conn.close()

    def detect_date_drift(
        self,
        df: pd.DataFrame,
        date_columns: List[str],
        max_age_days: int = 3650,  # 10 years
        max_future_days: int = 365  # 1 year
    ) -> Dict[str, Any]:
        """
        Detect date drift - timestamps that are too old or in the future

        Args:
            df: DataFrame with date columns
            date_columns: List of column names containing dates
            max_age_days: Maximum age for historical dates (default: 10 years)
            max_future_days: Maximum days into the future (default: 1 year)

        Returns:
            {
                'is_anomaly': bool,
                'severity': 'critical' | 'warning' | 'normal',
                'message': str,
                'details': {
                    'too_old_count': int,
                    'too_future_count': int,
                    'invalid_format_count': int,
                    'oldest_date': str,
                    'newest_date': str
                }
            }
        """
        now = datetime.now()
        min_allowed_date = now - timedelta(days=max_age_days)
        max_allowed_date = now + timedelta(days=max_future_days)

        too_old_count = 0
        too_future_count = 0
        invalid_format_count = 0
        all_dates = []

        for col in date_columns:
            if col not in df.columns:
                continue

            for val in df[col].dropna():
                try:
                    # Parse date (handle various formats)
                    if isinstance(val, str):
                        date_val = pd.to_datetime(val)
                    elif isinstance(val, datetime):
                        date_val = val
                    else:
                        invalid_format_count += 1
                        continue

                    all_dates.append(date_val)

                    # Check drift
                    if date_val < min_allowed_date:
                        too_old_count += 1
                    elif date_val > max_allowed_date:
                        too_future_count += 1

                except Exception:
                    invalid_format_count += 1

        total_anomalies = too_old_count + too_future_count + invalid_format_count

        if total_anomalies == 0:
            severity = 'normal'
            message = 'All dates within acceptable range'
        elif total_anomalies > len(df) * 0.1:  # >10% anomalies
            severity = 'critical'
            message = f'Severe date drift: {total_anomalies} anomalies ({too_old_count} too old, {too_future_count} future, {invalid_format_count} invalid)'
        else:
            severity = 'warning'
            message = f'Minor date drift: {total_anomalies} anomalies ({too_old_count} too old, {too_future_count} future, {invalid_format_count} invalid)'

        return {
            'is_anomaly': total_anomalies > 0,
            'severity': severity,
            'message': message,
            'details': {
                'too_old_count': too_old_count,
                'too_future_count': too_future_count,
                'invalid_format_count': invalid_format_count,
                'oldest_date': min(all_dates).isoformat() if all_dates else None,
                'newest_date': max(all_dates).isoformat() if all_dates else None
            }
        }

    def detect_malformed_headers(
        self,
        df: pd.DataFrame,
        expected_schema: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Detect malformed headers - missing/wrong columns

        Args:
            df: DataFrame to validate
            expected_schema: Dict of {column_name: expected_type}

        Returns:
            {
                'is_anomaly': bool,
                'severity': 'critical' | 'warning' | 'normal',
                'message': str,
                'missing_columns': List[str],
                'extra_columns': List[str],
                'type_mismatches': List[{column, expected, actual}]
            }
        """
        actual_columns = set(df.columns)
        expected_columns = set(expected_schema.keys())

        missing_columns = list(expected_columns - actual_columns)
        extra_columns = list(actual_columns - expected_columns)

        # Check data types for matching columns
        type_mismatches = []
        for col in expected_columns & actual_columns:
            expected_type = expected_schema[col]
            actual_type = str(df[col].dtype)

            # Simplified type matching
            if expected_type == 'int' and 'int' not in actual_type:
                type_mismatches.append({
                    'column': col,
                    'expected': expected_type,
                    'actual': actual_type
                })
            elif expected_type == 'float' and 'float' not in actual_type:
                type_mismatches.append({
                    'column': col,
                    'expected': expected_type,
                    'actual': actual_type
                })
            elif expected_type == 'str' and actual_type not in ['object', 'string']:
                type_mismatches.append({
                    'column': col,
                    'expected': expected_type,
                    'actual': actual_type
                })

        if missing_columns:
            severity = 'critical'
            message = f'Missing required columns: {", ".join(missing_columns)}'
        elif type_mismatches:
            severity = 'warning'
            message = f'Type mismatches in {len(type_mismatches)} columns'
        elif extra_columns:
            severity = 'warning'
            message = f'Extra columns detected: {", ".join(extra_columns)}'
        else:
            severity = 'normal'
            message = 'Schema validation passed'

        return {
            'is_anomaly': len(missing_columns) > 0 or len(type_mismatches) > 0,
            'severity': severity,
            'message': message,
            'missing_columns': missing_columns,
            'extra_columns': extra_columns,
            'type_mismatches': type_mismatches
        }

    def run_full_validation(
        self,
        df: pd.DataFrame,
        source: str,
        expected_schema: Optional[Dict[str, str]] = None,
        date_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run all anomaly detection checks

        Returns:
            {
                'overall_status': 'pass' | 'warning' | 'fail',
                'anomaly_count': int,
                'checks': {
                    'volume_spike': {...},
                    'date_drift': {...},
                    'malformed_headers': {...}
                },
                'summary': str
            }
        """
        checks = {}

        # Volume spike check
        checks['volume_spike'] = self.detect_volume_spike(len(df), source)

        # Date drift check (if date columns specified)
        if date_columns:
            checks['date_drift'] = self.detect_date_drift(df, date_columns)
        else:
            checks['date_drift'] = {
                'is_anomaly': False,
                'severity': 'normal',
                'message': 'Date validation skipped (no date columns specified)'
            }

        # Header validation (if schema specified)
        if expected_schema:
            checks['malformed_headers'] = self.detect_malformed_headers(df, expected_schema)
        else:
            checks['malformed_headers'] = {
                'is_anomaly': False,
                'severity': 'normal',
                'message': 'Schema validation skipped (no expected schema provided)'
            }

        # Overall assessment
        critical_count = sum(1 for check in checks.values() if check['severity'] == 'critical')
        warning_count = sum(1 for check in checks.values() if check['severity'] == 'warning')
        anomaly_count = sum(1 for check in checks.values() if check['is_anomaly'])

        if critical_count > 0:
            overall_status = 'fail'
            summary = f'{critical_count} critical issue(s) detected - upload may be rejected'
        elif warning_count > 0:
            overall_status = 'warning'
            summary = f'{warning_count} warning(s) detected - proceed with caution'
        else:
            overall_status = 'pass'
            summary = 'All validation checks passed'

        return {
            'overall_status': overall_status,
            'anomaly_count': anomaly_count,
            'checks': checks,
            'summary': summary
        }


def log_ingestion_event(
    filename: str,
    format_detected: str,
    rows_processed: int,
    status: str,
    anomaly_report: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None
) -> int:
    """
    Log ingestion event to ingestion_log table

    Args:
        filename: Name of uploaded file
        format_detected: Detected file format
        rows_processed: Number of rows processed
        status: 'success' | 'warning' | 'failed'
        anomaly_report: Optional anomaly detection report (JSON)
        error_message: Optional error message

    Returns:
        ingestion_id: ID of logged event
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO ingestion_log (
                filename,
                format_detected,
                rows_processed,
                upload_date,
                status,
                anomaly_report,
                error_message
            ) VALUES (%s, %s, %s, NOW(), %s, %s, %s)
            RETURNING ingestion_id
        """, (
            filename,
            format_detected,
            rows_processed,
            status,
            str(anomaly_report) if anomaly_report else None,
            error_message
        ))

        ingestion_id = cur.fetchone()[0]
        conn.commit()

        return ingestion_id

    finally:
        cur.close()
        conn.close()
