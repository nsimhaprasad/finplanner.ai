# Agent Models Documentation

This document outlines which agents use Google Gemini models and their specific use cases.

## Model Usage by Agent

### 🔥 **High-Complexity Agents (Gemini-1.5-Pro)**

#### 1. **CAS Parser Agent** (`gemini-1.5-pro`)
- **Purpose**: Extracts portfolio data from complex CAS PDF text
- **Why Pro**: 
  - Complex financial document parsing
  - Needs to understand various CAS formats
  - High accuracy required for financial data
  - Handles unstructured text with multiple tables

#### 2. **Financial Advisor Agent** (`gemini-1.5-pro`)
- **Purpose**: Generates comprehensive financial recommendations
- **Why Pro**:
  - Complex reasoning across multiple data points
  - Personalized advice generation
  - Risk-adjusted recommendations
  - Regulatory compliance considerations

### ⚡ **Standard Agents (Gemini-1.5-Flash)**

#### 3. **Portfolio Analyzer Agent** (`gemini-1.5-flash`)
- **Purpose**: Analyzes portfolio composition and risks
- **Why Flash**: Fast analysis of structured portfolio data

#### 4. **Market Outlook Agent** (`gemini-1.5-flash`)
- **Purpose**: Analyzes market data and trends
- **Why Flash**: Real-time data processing and sentiment analysis

#### 5. **Risk Profiler Agent** (`gemini-1.5-flash`)
- **Purpose**: Assesses user risk tolerance
- **Why Flash**: Structured questionnaire analysis

## Cost Optimization Strategy

### **Gemini-1.5-Pro Usage** (2 agents)
- Used for complex tasks requiring deep reasoning
- Higher cost but essential for accuracy
- ~20% of total LLM calls

### **Gemini-1.5-Flash Usage** (3 agents)
- Used for standard analysis tasks
- Cost-effective and fast
- ~80% of total LLM calls

## API Key Requirements

### **Required Environment Variable**
```bash
GOOGLE_API_KEY=your_google_ai_studio_api_key
```

### **How to Get API Key**
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a new project or select existing
3. Generate API key
4. Add to your `.env` file

### **Free Tier Limits** (Google AI Studio)
- **Gemini-1.5-Flash**: 15 requests/minute, 1M requests/day
- **Gemini-1.5-Pro**: 2 requests/minute, 50 requests/day

## Workflow Model Usage

```
Upload PDF → CAS Parser (Pro) → Portfolio Analyzer (Flash) 
    ↓
Market Outlook (Flash) → Risk Profiler (Flash) → Financial Advisor (Pro)
```

## Performance Characteristics

| Agent | Model | Speed | Accuracy | Cost | Use Case |
|-------|-------|-------|----------|------|-----------|
| CAS Parser | Pro | Slower | High | Higher | Complex PDF parsing |
| Portfolio Analyzer | Flash | Fast | Good | Lower | Structured analysis |
| Market Outlook | Flash | Fast | Good | Lower | Real-time data |
| Risk Profiler | Flash | Fast | Good | Lower | Questionnaire analysis |
| Financial Advisor | Pro | Slower | High | Higher | Complex recommendations |

## Fallback Strategy

If Google API fails or quota exceeded:
- Agents fall back to mock/default data
- System continues to function
- Error handling ensures graceful degradation