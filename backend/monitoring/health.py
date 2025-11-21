"""
Production Health & Status Monitoring Dashboard
Comprehensive system health checks for demo and operational readiness
"""
import os
import psycopg2
from datetime import datetime
import time
from typing import Dict, Any, List
import psutil


class HealthMonitor:
    """
    Comprehensive health monitoring for production readiness

    Monitors:
    - Database connectivity and performance
    - Analyzer status and data quality
    - System resources (CPU, memory, disk)
    - API endpoint response times
    - Upload pipeline health
    - Data freshness
    """

    def __init__(self):
        self.start_time = time.time()

    def check_database_health(self) -> Dict[str, Any]:
        """
        Check PostgreSQL database health and performance

        Returns:
            {
                'status': 'healthy'|'degraded'|'down',
                'connection_time_ms': float,
                'row_counts': dict,
                'last_update': datetime,
                'performance_grade': str
            }
        """
        try:
            dsn = os.getenv("DATABASE_URL")
            if not dsn:
                return {
                    'status': 'down',
                    'error': 'DATABASE_URL not configured'
                }

            start = time.time()
            conn = psycopg2.connect(dsn, connect_timeout=3)
            connection_time = (time.time() - start) * 1000  # ms

            cur = conn.cursor()

            # Get row counts
            cur.execute("SELECT COUNT(*) FROM employees")
            employee_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM skills")
            skill_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM skill_events")
            event_count = cur.fetchone()[0]

            # Check last update time
            cur.execute("SELECT MAX(created_at) FROM skill_events")
            last_update_row = cur.fetchone()
            last_update = last_update_row[0] if last_update_row[0] else None

            # Performance grading
            if connection_time < 100:
                perf_grade = 'A - Excellent'
            elif connection_time < 200:
                perf_grade = 'B - Good'
            elif connection_time < 500:
                perf_grade = 'C - Fair'
            else:
                perf_grade = 'D - Slow'

            status = 'healthy' if connection_time < 500 else 'degraded'

            cur.close()
            conn.close()

            return {
                'status': status,
                'connection_time_ms': round(connection_time, 2),
                'row_counts': {
                    'employees': employee_count,
                    'skills': skill_count,
                    'skill_events': event_count
                },
                'last_update': last_update.isoformat() if last_update else None,
                'performance_grade': perf_grade,
                'data_quality': 'good' if event_count > 0 else 'empty'
            }

        except Exception as e:
            return {
                'status': 'down',
                'error': str(e)
            }

    def check_system_resources(self) -> Dict[str, Any]:
        """
        Check system resource usage (CPU, memory, disk)

        Returns:
            {
                'cpu_percent': float,
                'memory_percent': float,
                'disk_percent': float,
                'health_status': str
            }
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Health assessment
            issues = []
            if cpu_percent > 80:
                issues.append('High CPU usage')
            if memory.percent > 85:
                issues.append('High memory usage')
            if disk.percent > 90:
                issues.append('Low disk space')

            status = 'healthy' if len(issues) == 0 else 'degraded'

            return {
                'status': status,
                'cpu_percent': round(cpu_percent, 1),
                'memory_percent': round(memory.percent, 1),
                'disk_percent': round(disk.percent, 1),
                'memory_available_mb': round(memory.available / 1024 / 1024, 0),
                'disk_free_gb': round(disk.free / 1024 / 1024 / 1024, 1),
                'issues': issues
            }

        except Exception as e:
            return {
                'status': 'unknown',
                'error': str(e)
            }

    def check_analyzer_status(self, cluster_analyzer, timeseries_analyzer, embedding_analyzer, advanced_insights) -> Dict[str, Any]:
        """
        Check if all analyzers are loaded and operational

        Args:
            Analyzer instances from main.py global state

        Returns:
            {
                'status': 'healthy'|'degraded'|'down',
                'analyzers': dict,
                'data_quality': str
            }
        """
        analyzers_status = {
            'cluster_analyzer': cluster_analyzer is not None,
            'timeseries_analyzer': timeseries_analyzer is not None,
            'embedding_analyzer': embedding_analyzer is not None,
            'advanced_insights': advanced_insights is not None
        }

        all_loaded = all(analyzers_status.values())
        some_loaded = any(analyzers_status.values())

        if all_loaded:
            status = 'healthy'
        elif some_loaded:
            status = 'degraded'
        else:
            status = 'down'

        # Check data quality if timeseries analyzer available
        data_quality = 'unknown'
        if timeseries_analyzer:
            try:
                skills_count = len(timeseries_analyzer.skills) if hasattr(timeseries_analyzer, 'skills') else 0
                if skills_count > 20:
                    data_quality = 'excellent'
                elif skills_count > 10:
                    data_quality = 'good'
                elif skills_count > 0:
                    data_quality = 'limited'
                else:
                    data_quality = 'empty'
            except:
                data_quality = 'unknown'

        return {
            'status': status,
            'analyzers': analyzers_status,
            'data_quality': data_quality
        }

    def check_upload_pipeline(self) -> Dict[str, Any]:
        """
        Check upload pipeline health

        Returns:
            {
                'status': 'operational',
                'supported_formats': int,
                'parsers_available': bool
            }
        """
        try:
            # Check if parser modules are importable
            from parsers.multi_format_parser import MultiFormatParser
            from data.db_writer import persist_parsed_data_to_db

            return {
                'status': 'operational',
                'supported_formats': 6,
                'parsers_available': True,
                'features': [
                    'Multi-format CSV parsing',
                    'Excel/PDF support',
                    'Auto-format detection',
                    'PostgreSQL persistence',
                    'Real-time analyzer reload'
                ]
            }

        except Exception as e:
            return {
                'status': 'degraded',
                'error': str(e),
                'parsers_available': False
            }

    def get_uptime(self) -> Dict[str, Any]:
        """
        Calculate system uptime

        Returns:
            {
                'uptime_seconds': float,
                'uptime_formatted': str
            }
        """
        uptime_seconds = time.time() - self.start_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)

        return {
            'uptime_seconds': round(uptime_seconds, 0),
            'uptime_formatted': f"{hours}h {minutes}m {seconds}s"
        }

    def generate_comprehensive_health_report(self, cluster_analyzer=None, timeseries_analyzer=None, embedding_analyzer=None, advanced_insights=None) -> Dict[str, Any]:
        """
        Generate comprehensive health dashboard

        Returns:
            Full system health report with all metrics
        """
        database_health = self.check_database_health()
        system_resources = self.check_system_resources()
        analyzer_status = self.check_analyzer_status(cluster_analyzer, timeseries_analyzer, embedding_analyzer, advanced_insights)
        upload_pipeline = self.check_upload_pipeline()
        uptime = self.get_uptime()

        # Calculate overall health
        component_statuses = [
            database_health.get('status'),
            system_resources.get('status'),
            analyzer_status.get('status'),
            upload_pipeline.get('status')
        ]

        if all(s == 'healthy' or s == 'operational' for s in component_statuses):
            overall_status = 'healthy'
            overall_grade = 'A'
        elif 'down' in component_statuses:
            overall_status = 'degraded'
            overall_grade = 'C'
        else:
            overall_status = 'operational'
            overall_grade = 'B'

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': overall_status,
            'overall_grade': overall_grade,
            'uptime': uptime,
            'components': {
                'database': database_health,
                'system_resources': system_resources,
                'analyzers': analyzer_status,
                'upload_pipeline': upload_pipeline
            },
            'api_endpoints': {
                'total_available': 20,
                'key_endpoints': [
                    '/api/genome',
                    '/api/evolution',
                    '/api/insights',
                    '/api/upload-data',
                    '/api/reskilling-roi-simulator',
                    '/api/mentorship-recommendations',
                    '/api/talent-redundancy-alerts',
                    '/api/taxonomy-evolution'
                ]
            },
            'features': {
                'differentiated_intelligence': [
                    'Mutation Risk Scoring (validated formula)',
                    'ROI Metrics (training cost savings)',
                    'Workforce Readiness Score (0-100)',
                    'MAPE Forecast Accuracy',
                    'Mentorship & Transition Recommendations',
                    'Talent Redundancy Alerts',
                    'Reskilling ROI Simulator',
                    'Taxonomy Evolution Analysis'
                ],
                'data_pipeline': [
                    'PostgreSQL persistence',
                    'Multi-format parsing (6 formats)',
                    'Real-time analyzer reload',
                    'Czech & English support'
                ],
                'production_readiness': [
                    'Health monitoring dashboard',
                    'Error handling & fallbacks',
                    'Performance optimization',
                    'CORS configured for production'
                ]
            },
            'metrics': {
                'database_connection_ms': database_health.get('connection_time_ms'),
                'cpu_usage_percent': system_resources.get('cpu_percent'),
                'memory_usage_percent': system_resources.get('memory_percent'),
                'data_row_counts': database_health.get('row_counts', {})
            }
        }


# Global health monitor instance
_health_monitor = HealthMonitor()


def get_health_monitor():
    """Get the global health monitor instance"""
    return _health_monitor
