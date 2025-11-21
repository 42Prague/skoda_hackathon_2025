"""Add skill coach models

Revision ID: skill_coach_001
Revises: 
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql
import sqlmodel

# revision identifiers, used by Alembic.
revision = "skill_coach_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration changes."""
    # Create employee_record table
    op.create_table(
        'employee_record',
        sa.Column('employee_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('department', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('skills', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_employee_record_employee_id'), 'employee_record', ['employee_id'], unique=True)
    op.create_index(op.f('ix_employee_record_department'), 'employee_record', ['department'], unique=False)
    
    # Create skill_analysis_record table
    op.create_table(
        'skill_analysis_record',
        sa.Column('employee_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('analysis_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('recommendations_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_skill_analysis_record_employee_id'), 'skill_analysis_record', ['employee_id'], unique=False)
    
    # Create dataset_record table
    op.create_table(
        'dataset_record',
        sa.Column('dataset_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('dq_score', sa.Integer(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_record_dataset_id'), 'dataset_record', ['dataset_id'], unique=True)
    
    # Create learning_history table
    op.create_table(
        'learning_history',
        sa.Column('employee_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('course_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('provider', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('hours', sa.Float(), nullable=True),
        sa.Column('completion_status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False, server_default='in_progress'),
        sa.Column('skills_covered', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('certificate_url', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employee_record.employee_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_learning_history_employee_id'), 'learning_history', ['employee_id'], unique=False)
    
    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('event_type', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('service_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('user_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('ip_address', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_log_event_type'), 'audit_log', ['event_type'], unique=False)


def downgrade():
    """Revert migration changes."""
    op.drop_index(op.f('ix_audit_log_event_type'), table_name='audit_log')
    op.drop_table('audit_log')
    op.drop_index(op.f('ix_learning_history_employee_id'), table_name='learning_history')
    op.drop_table('learning_history')
    op.drop_index(op.f('ix_dataset_record_dataset_id'), table_name='dataset_record')
    op.drop_table('dataset_record')
    op.drop_index(op.f('ix_skill_analysis_record_employee_id'), table_name='skill_analysis_record')
    op.drop_table('skill_analysis_record')
    op.drop_index(op.f('ix_employee_record_department'), table_name='employee_record')
    op.drop_index(op.f('ix_employee_record_employee_id'), table_name='employee_record')
    op.drop_table('employee_record')

