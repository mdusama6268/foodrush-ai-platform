# 🚀 FoodRush AI Platform

### AI-powered Food Delivery Operations Assistant  
Built by Huzefa — Food Delivery Operations Experience + AI Automation Skills

## Project Overview

FoodRush AI Platform is an AI-powered operations assistant built for food delivery businesses.

The system can answer company policy questions, classify customer complaints, calculate rider requirements, split rider planning by peak time, and generate executive-level operations insights.

## Main Features

### 1. Policy Assistant

Answers questions from FoodRush business policies:

- Delivery policy
- Refund policy
- Driver guidelines
- Customer support policy
- Restaurant policy

### 2. Operations Agent

Helps operations teams calculate:

- Expected orders today
- Riders needed for full-day operations
- Rider capacity per shift
- Recommended riders with buffer

### 3. Peak-Time Rider Planning

Splits demand by peak time windows:

- Breakfast
- Lunch Peak
- Evening Peak
- Late Orders

### 4. Hot Weather Operations Plan

If temperature is high, the system adjusts:

- Delivery time assumption
- Rider buffer
- Customer ETA strategy
- Promotion recommendations

### 5. Complaint Manager

Classifies customer complaints into:

- Delay
- Wrong order
- Refund issue
- Food quality issue
- General complaint

### 6. Executive Dashboard

Generates business-level operations summary for managers.

## Example Questions

What is the refund policy for late orders?

How many riders need today?

Can be split into the peak time wise?

If weather is 40 degree then?

My order is 2 hours late and food is cold.

Give me today's complete operations briefing.

## Tech Stack

- Python
- FastAPI
- LangChain
- Groq LLM
- Pydantic
- Render Deployment

## API Endpoints

Home:

GET /

Health Check:

GET /health

Ask FoodRush AI:

POST /ask

Example request:

{
  "question": "how many riders need today"
}

## Sample Business Logic

Normal operations:

Expected Orders Today: 250  
Average Delivery Time: 30 minutes  
Normal Buffer: 20%

Hot weather:

Temperature: 40°C  
Average Delivery Time: 40 minutes  
Hot Weather Buffer: 30%

## Why This Project Matters

Most AI demos are simple chatbots.

This project is different because it uses real operations logic from food delivery business experience.

It shows how AI can support:

- Rider planning
- Complaint routing
- Policy answering
- Peak-time decision making
- Executive operations reporting

## About Me

I have food delivery operations experience and I am building AI automation solutions for real business problems.

My focus is combining domain knowledge with AI tools to create practical automation systems.

## Contact

LinkedIn: Add your LinkedIn link  
Email: Add your email
