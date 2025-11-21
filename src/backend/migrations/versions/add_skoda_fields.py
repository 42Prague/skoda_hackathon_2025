"""Add Škoda fields and tables

Revision ID: skoda_fields_001
Revises: skill_coach_001
Create Date: 2025-11-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql
import sqlmodel

# revision identifiers, used by Alembic.
revision = "skoda_fields_001"
down_revision = "skill_coach_001"
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration changes."""
    # Add Škoda fields to employee_record
    op.add_column('employee_record', sa.Column('personal_number', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    op.add_column('employee_record', sa.Column('persstat_start_month_abc', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True))
    op.add_column('employee_record', sa.Column('pers_organization_branch', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    op.add_column('employee_record', sa.Column('pers_profession_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    op.add_column('employee_record', sa.Column('pers_job_family_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    op.add_column('employee_record', sa.Column('s1_org_hierarchy', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True))
    op.add_column('employee_record', sa.Column('s2_org_hierarchy', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True))
    op.add_column('employee_record', sa.Column('s3_org_hierarchy', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True))
    op.add_column('employee_record', sa.Column('s4_org_hierarchy', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True))
    
    op.create_index(op.f('ix_employee_record_personal_number'), 'employee_record', ['personal_number'], unique=False)
    op.create_index(op.f('ix_employee_record_pers_job_family_id'), 'employee_record', ['pers_job_family_id'], unique=False)
    
    # Create qualification_record table
    op.create_table(
        'qualification_record',
        sa.Column('employee_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('qualification_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('qualification_name_cz', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('qualification_name_en', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('mandatory', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('obtained_date', sa.DateTime(), nullable=True),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False, server_default='active'),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employee_record.employee_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_qualification_record_employee_id'), 'qualification_record', ['employee_id'], unique=False)
    op.create_index(op.f('ix_qualification_record_qualification_id'), 'qualification_record', ['qualification_id'], unique=False)
    
    # Create job_family_record table
    op.create_table(
        'job_family_record',
        sa.Column('job_family_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('job_family_name_cz', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('job_family_name_en', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('required_qualifications', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('required_skills', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('preferred_skills', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_family_record_job_family_id'), 'job_family_record', ['job_family_id'], unique=True)
    
    # Create org_hierarchy_record table
    op.create_table(
        'org_hierarchy_record',
        sa.Column('employee_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('hierarchy_path', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=False),
        sa.Column('hierarchy_name_cz', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('hierarchy_name_en', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employee_record.employee_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_org_hierarchy_record_employee_id'), 'org_hierarchy_record', ['employee_id'], unique=False)
    op.create_index(op.f('ix_org_hierarchy_record_level'), 'org_hierarchy_record', ['level'], unique=False)
    op.create_index(op.f('ix_org_hierarchy_record_path'), 'org_hierarchy_record', ['hierarchy_path'], unique=False)
    
    # Create course_catalog_record table
    op.create_table(
        'course_catalog_record',
        sa.Column('course_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('course_name_cz', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('course_name_en', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('provider', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('duration_hours', sa.Float(), nullable=True),
        sa.Column('skills_covered', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('qualifications_granted', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('skoda_academy', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_course_catalog_record_course_id'), 'course_catalog_record', ['course_id'], unique=True)
    
    # Create skill_mapping_record table
    op.create_table(
        'skill_mapping_record',
        sa.Column('raw_skill_name', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('normalized_skill_name', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('language', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column('synonyms', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('canonical_skill_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_skill_mapping_record_raw'), 'skill_mapping_record', ['raw_skill_name'], unique=False)
    op.create_index(op.f('ix_skill_mapping_record_normalized'), 'skill_mapping_record', ['normalized_skill_name'], unique=False)
    op.create_index(op.f('ix_skill_mapping_record_canonical'), 'skill_mapping_record', ['canonical_skill_id'], unique=False)
    
    # Create historical_employee_snapshot table
    op.create_table(
        'historical_employee_snapshot',
        sa.Column('employee_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(), nullable=False),
        sa.Column('department', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('job_family_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('org_hierarchy', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('skills', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('qualifications', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('pers_profession_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('pers_organization_branch', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['employee_id'], ['employee_record.employee_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_historical_snapshot_employee_id'), 'historical_employee_snapshot', ['employee_id'], unique=False)
    op.create_index(op.f('ix_historical_snapshot_date'), 'historical_employee_snapshot', ['snapshot_date'], unique=False)
    op.create_index(op.f('ix_historical_snapshot_employee_date'), 'historical_employee_snapshot', ['employee_id', 'snapshot_date'], unique=False)
    
    # Add course_catalog_id to learning_history
    op.add_column('learning_history', sa.Column('course_catalog_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    op.create_index(op.f('ix_learning_history_course_catalog_id'), 'learning_history', ['course_catalog_id'], unique=False)


def downgrade():
    """Revert migration changes."""
    op.drop_index(op.f('ix_learning_history_course_catalog_id'), table_name='learning_history')
    op.drop_column('learning_history', 'course_catalog_id')
    
    op.drop_index(op.f('ix_historical_snapshot_employee_date'), table_name='historical_employee_snapshot')
    op.drop_index(op.f('ix_historical_snapshot_date'), table_name='historical_employee_snapshot')
    op.drop_index(op.f('ix_historical_snapshot_employee_id'), table_name='historical_employee_snapshot')
    op.drop_table('historical_employee_snapshot')
    
    op.drop_index(op.f('ix_skill_mapping_record_canonical'), table_name='skill_mapping_record')
    op.drop_index(op.f('ix_skill_mapping_record_normalized'), table_name='skill_mapping_record')
    op.drop_index(op.f('ix_skill_mapping_record_raw'), table_name='skill_mapping_record')
    op.drop_table('skill_mapping_record')
    
    op.drop_index(op.f('ix_course_catalog_record_course_id'), table_name='course_catalog_record')
    op.drop_table('course_catalog_record')
    
    op.drop_index(op.f('ix_org_hierarchy_record_path'), table_name='org_hierarchy_record')
    op.drop_index(op.f('ix_org_hierarchy_record_level'), table_name='org_hierarchy_record')
    op.drop_index(op.f('ix_org_hierarchy_record_employee_id'), table_name='org_hierarchy_record')
    op.drop_table('org_hierarchy_record')
    
    op.drop_index(op.f('ix_job_family_record_job_family_id'), table_name='job_family_record')
    op.drop_table('job_family_record')
    
    op.drop_index(op.f('ix_qualification_record_qualification_id'), table_name='qualification_record')
    op.drop_index(op.f('ix_qualification_record_employee_id'), table_name='qualification_record')
    op.drop_table('qualification_record')
    
    op.drop_index(op.f('ix_employee_record_pers_job_family_id'), table_name='employee_record')
    op.drop_index(op.f('ix_employee_record_personal_number'), table_name='employee_record')
    op.drop_column('employee_record', 's4_org_hierarchy')
    op.drop_column('employee_record', 's3_org_hierarchy')
    op.drop_column('employee_record', 's2_org_hierarchy')
    op.drop_column('employee_record', 's1_org_hierarchy')
    op.drop_column('employee_record', 'pers_job_family_id')
    op.drop_column('employee_record', 'pers_profession_id')
    op.drop_column('employee_record', 'pers_organization_branch')
    op.drop_column('employee_record', 'persstat_start_month_abc')
    op.drop_column('employee_record', 'personal_number')

