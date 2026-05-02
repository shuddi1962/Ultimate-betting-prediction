"""Initial migration

Revision ID: initial
Revises: 
Create Date: 2026-05-02

"""
from alembic import op
import sqlalchemy as sa

revision = 'initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('leagues',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('external_id', sa.String(50), unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('country', sa.String(100)),
        sa.Column('logo_url', sa.String(500)),
        sa.Column('season_year', sa.Integer()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )
    
    op.create_table('teams',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('external_id', sa.String(50), unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('short_name', sa.String(50)),
        sa.Column('logo_url', sa.String(500)),
        sa.Column('venue_name', sa.String(200)),
        sa.Column('founded', sa.Integer()),
        sa.Column('market_value', sa.Float()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )
    
    op.create_table('fixtures',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('external_id', sa.String(50), unique=True),
        sa.Column('league_id', sa.Integer(), sa.ForeignKey('leagues.id')),
        sa.Column('home_team_id', sa.Integer(), sa.ForeignKey('teams.id')),
        sa.Column('away_team_id', sa.Integer(), sa.ForeignKey('teams.id')),
        sa.Column('kickoff_utc', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(10), default='NS'),
        sa.Column('home_score', sa.Integer()),
        sa.Column('away_score', sa.Integer()),
        sa.Column('home_ht_score', sa.Integer()),
        sa.Column('away_ht_score', sa.Integer()),
        sa.Column('home_goals', sa.Integer()),
        sa.Column('away_goals', sa.Integer()),
        sa.Column('home_xg', sa.Float()),
        sa.Column('away_xg', sa.Float()),
        sa.Column('home_shots', sa.Integer()),
        sa.Column('away_shots', sa.Integer()),
        sa.Column('home_shots_on_target', sa.Integer()),
        sa.Column('away_shots_on_target', sa.Integer()),
        sa.Column('home_possession', sa.Float()),
        sa.Column('away_possession', sa.Float()),
        sa.Column('home_corners', sa.Integer()),
        sa.Column('away_corners', sa.Integer()),
        sa.Column('home_fouls', sa.Integer()),
        sa.Column('away_fouls', sa.Integer()),
        sa.Column('home_yellow_cards', sa.Integer()),
        sa.Column('away_yellow_cards', sa.Integer()),
        sa.Column('home_red_cards', sa.Integer()),
        sa.Column('away_red_cards', sa.Integer()),
        sa.Column('home_formation', sa.String(20)),
        sa.Column('away_formation', sa.String(20)),
        sa.Column('round', sa.String(50)),
        sa.Column('referee', sa.String(100)),
        sa.Column('venue', sa.String(200)),
        sa.Column('source', sa.String(50)),
        sa.Column('scraped_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_table('predictions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('fixture_id', sa.Integer(), sa.ForeignKey('fixtures.id')),
        sa.Column('home_win_prob', sa.Float()),
        sa.Column('draw_prob', sa.Float()),
        sa.Column('away_win_prob', sa.Float()),
        sa.Column('expected_home_goals', sa.Float()),
        sa.Column('expected_away_goals', sa.Float()),
        sa.Column('expected_total_goals', sa.Float()),
        sa.Column('btts_yes_prob', sa.Float()),
        sa.Column('over_2_5_prob', sa.Float()),
        sa.Column('over_1_5_prob', sa.Float()),
        sa.Column('over_3_5_prob', sa.Float()),
        sa.Column('recommended_market', sa.String(50)),
        sa.Column('recommended_pick', sa.String(100)),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('primary_reason', sa.String(500)),
        sa.Column('why_not_home', sa.String(500)),
        sa.Column('why_not_draw', sa.String(500)),
        sa.Column('why_not_away', sa.String(500)),
        sa.Column('key_risks', sa.JSON()),
        sa.Column('data_sources_used', sa.JSON()),
        sa.Column('data_completeness', sa.Float()),
        sa.Column('model_agreement', sa.Float()),
        sa.Column('score_matrix', sa.JSON()),
        sa.Column('outcome_correct', sa.Boolean()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

def downgrade():
    op.drop_table('predictions')
    op.drop_table('fixtures')
    op.drop_table('teams')
    op.drop_table('leagues')
