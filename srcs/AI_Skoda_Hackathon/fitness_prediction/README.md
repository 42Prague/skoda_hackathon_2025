# Fitness Prediction Scripts

Python scripts for predicting employee fitness scores for job positions using Azure OpenAI.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure OpenAI credentials
```

## Usage

### Predict Single Employee
```bash
python predict_employee_fitness.py <employee_id> <target_position>
```

### Batch Predictions
```bash
python batch_predict_positions.py
```

### Calculate IT Fitness Scores
```bash
python calculate_it_fitness_scores.py
```

## Configuration

Required environment variables in `.env`:

```bash
AZURE_OPENAI_API_URL=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT=hackathon-gpt-4.1
```

## Data Files

Scripts expect CSV data files in `../data/` directory:
- Employee master data
- Skills and qualifications
- Courses and training
- Position requirements

See main project README for data setup instructions.
