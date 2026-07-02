import os
import math
import re

from fastapi import FastAPI
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


app = FastAPI(
    title="FoodRush AI Platform",
    description="AI-powered food delivery operations platform using FastAPI, LangChain, and Groq.",
    version="1.0.0"
)


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0.2
    )
else:
    llm = None


POLICY_DOCUMENTS = [
    """
    FoodRush Delivery Policy:
    Standard delivery time is 30-45 minutes.
    Express delivery takes 20 minutes and costs ₹50 extra.
    Delivery is free above ₹299.
    Delivery charge is ₹30 for orders below ₹299.
    Delivery is available from 8 AM to 11 PM.
    Maximum delivery radius is 10 km.
    """,

    """
    FoodRush Refund Policy:
    Full refund is given if the order is more than 60 minutes late.
    50% refund is given if the order is 30-60 minutes late.
    Full refund is given for wrong orders.
    Refund is processed within 24-48 hours.
    No refund is given after food preparation starts, except for late or wrong orders.
    """,

    """
    FoodRush Driver Guidelines:
    Drivers must maintain minimum 4.0 rating.
    Maximum 12 deliveries are allowed per shift.
    Standard shift duration is 8 hours.
    Driver base pay is ₹15 per delivery.
    Driver gets ₹5 bonus per delivery after completing more than 10 deliveries.
    Drivers must wear uniform and carry ID card.
    """,

    """
    FoodRush Customer Support Policy:
    Customer support is available from 8 AM to 11 PM.
    Normal response time is 30 minutes.
    High priority issues must be handled within 2 hours.
    Minimum customer satisfaction score is 4.2.
    Customers with 10 or more orders get priority support.
    """,

    """
    FoodRush Restaurant Policy:
    Restaurants must maintain minimum 4.0 rating.
    Food should be ready within 20 minutes.
    FoodRush charges 15% commission from restaurants.
    Restaurant payment is settled every 7 days.
    Menu can be updated twice per week.
    Restaurant audit is done every 3 months.
    """
]


def retrieve_policy_context(question: str, top_k: int = 3):
    question_words = set(question.lower().split())
    scored_docs = []

    for doc in POLICY_DOCUMENTS:
        doc_words = set(doc.lower().split())
        score = len(question_words.intersection(doc_words))
        scored_docs.append((score, doc))

    scored_docs.sort(reverse=True, key=lambda x: x[0])
    selected_docs = [doc for score, doc in scored_docs[:top_k]]

    return "\n".join(selected_docs)


FOODRUSH_OPS_DATA = {
    "city": "Bhopal",
    "expected_orders_today": 250,
    "base_delivery_time": 30,
    "shift_hours": 8,
    "normal_buffer": 0.20,
    "hot_weather_buffer": 0.30,
    "peak_windows": [
        {"name": "Breakfast", "time": "8 AM - 11 AM", "order_share": 0.15},
        {"name": "Lunch Peak", "time": "12 PM - 3 PM", "order_share": 0.35},
        {"name": "Evening Peak", "time": "6 PM - 10 PM", "order_share": 0.40},
        {"name": "Late Orders", "time": "10 PM - 11 PM", "order_share": 0.10},
    ]
}


def extract_temperature(question):
    match = re.search(
        r"(\d+)\s*(degree|degrees|°c|celsius|c)",
        question.lower()
    )

    if match:
        return int(match.group(1))

    return None


def calculate_riders_for_window(orders, delivery_time, window_hours, buffer):
    window_minutes = window_hours * 60
    deliveries_per_rider = max(1, int(window_minutes // delivery_time))
    base_riders = math.ceil(orders / deliveries_per_rider)
    riders_with_buffer = math.ceil(base_riders * (1 + buffer))

    return base_riders, riders_with_buffer, deliveries_per_rider


def daily_rider_plan(temp=None):
    orders = FOODRUSH_OPS_DATA["expected_orders_today"]
    delivery_time = FOODRUSH_OPS_DATA["base_delivery_time"]
    shift_hours = FOODRUSH_OPS_DATA["shift_hours"]

    if temp and temp >= 40:
        delivery_time = 40
        buffer = FOODRUSH_OPS_DATA["hot_weather_buffer"]
        weather_note = "Hot weather scenario: delivery time increased to 40 minutes and buffer increased to 30%."
    else:
        buffer = FOODRUSH_OPS_DATA["normal_buffer"]
        weather_note = "Normal scenario: delivery time is 30 minutes and buffer is 20%."

    deliveries_per_rider = (shift_hours * 60) // delivery_time
    base_riders = math.ceil(orders / deliveries_per_rider)
    riders_with_buffer = math.ceil(base_riders * (1 + buffer))

    return {
        "city": FOODRUSH_OPS_DATA["city"],
        "expected_orders_today": orders,
        "average_delivery_time_minutes": delivery_time,
        "deliveries_per_rider_per_shift": deliveries_per_rider,
        "base_riders_needed": base_riders,
        "recommended_riders_with_buffer": riders_with_buffer,
        "reason": weather_note
    }


def get_exact_peak_order_split():
    total_orders = FOODRUSH_OPS_DATA["expected_orders_today"]
    raw_orders = []

    for window in FOODRUSH_OPS_DATA["peak_windows"]:
        raw_orders.append(total_orders * window["order_share"])

    rounded_orders = [int(x) for x in raw_orders]
    remaining_orders = total_orders - sum(rounded_orders)

    decimal_parts = []

    for i in range(len(raw_orders)):
        decimal = raw_orders[i] - int(raw_orders[i])
        decimal_parts.append((i, decimal))

    decimal_parts.sort(key=lambda x: x[1], reverse=True)

    for i in range(remaining_orders):
        index = decimal_parts[i][0]
        rounded_orders[index] += 1

    return rounded_orders


def peak_time_rider_plan(temp=None):
    total_orders = FOODRUSH_OPS_DATA["expected_orders_today"]

    if temp and temp >= 40:
        delivery_time = 40
        buffer = FOODRUSH_OPS_DATA["hot_weather_buffer"]
        scenario = "40°C hot weather scenario: slower delivery and higher rider buffer."
    else:
        delivery_time = FOODRUSH_OPS_DATA["base_delivery_time"]
        buffer = FOODRUSH_OPS_DATA["normal_buffer"]
        scenario = "Normal weather scenario."

    exact_orders = get_exact_peak_order_split()

    peak_result = []
    highest_rider_need = 0
    highest_window_name = ""
    total_split_orders = 0

    for index, window in enumerate(FOODRUSH_OPS_DATA["peak_windows"]):
        orders = exact_orders[index]
        total_split_orders += orders

        if window["name"] == "Breakfast":
            window_hours = 3
        elif window["name"] == "Lunch Peak":
            window_hours = 3
        elif window["name"] == "Evening Peak":
            window_hours = 4
        else:
            window_hours = 1

        base_riders, riders_with_buffer, capacity = calculate_riders_for_window(
            orders=orders,
            delivery_time=delivery_time,
            window_hours=window_hours,
            buffer=buffer
        )

        if riders_with_buffer > highest_rider_need:
            highest_rider_need = riders_with_buffer
            highest_window_name = window["name"]

        peak_result.append({
            "window": window["name"],
            "time": window["time"],
            "expected_orders": orders,
            "per_rider_capacity": capacity,
            "base_riders_needed": base_riders,
            "recommended_riders_with_buffer": riders_with_buffer
        })

    return {
        "city": FOODRUSH_OPS_DATA["city"],
        "expected_orders_today": total_orders,
        "average_delivery_time_minutes": delivery_time,
        "buffer_percent": int(buffer * 100),
        "scenario": scenario,
        "important_note": "Peak-time rider numbers show riders needed during each specific time window. Do not add all windows together.",
        "peak_windows": peak_result,
        "total_split_orders_check": f"{total_split_orders}/{total_orders}",
        "highest_peak_window": highest_window_name,
        "highest_peak_rider_requirement": highest_rider_need
    }


def hot_weather_plan(temp):
    return {
        "hot_weather_temperature": temp,
        "impact": [
            "Delivery speed may reduce because riders need more breaks.",
            "Food quality risk increases for cold drinks, ice creams, and fresh items.",
            "Customer complaints may increase if ETAs are not adjusted."
        ],
        "recommended_actions": [
            "Increase rider buffer from 20% to 30%.",
            "Increase average delivery time assumption from 30 minutes to 40 minutes.",
            "Push cold drinks, ice creams, and summer combo offers.",
            "Show realistic ETA to customers.",
            "Keep more riders near high-demand restaurant zones."
        ],
        "daily_rider_plan": daily_rider_plan(temp=temp),
        "peak_time_rider_plan": peak_time_rider_plan(temp=temp)
    }


def route_query(question):
    q = question.lower()

    complaint_words = [
        "late", "delay", "wrong", "refund", "cold", "bad food",
        "complaint", "money", "payment issue", "not received"
    ]

    dashboard_words = [
        "dashboard", "briefing", "summary", "today's report",
        "operations briefing", "complete report", "executive"
    ]

    operations_words = [
        "weather", "drivers", "driver", "rider", "riders",
        "orders", "capacity", "how many drivers", "how many riders",
        "fleet", "planning", "peak", "peak time", "split",
        "temperature", "degree", "40 degree", "hot weather"
    ]

    policy_words = [
        "policy", "delivery policy", "refund policy", "restaurant policy",
        "driver guidelines", "support policy", "commission", "free delivery"
    ]

    if any(word in q for word in dashboard_words):
        return "DASHBOARD"

    if any(word in q for word in complaint_words):
        return "COMPLAINT"

    if any(word in q for word in operations_words):
        return "OPERATIONS"

    if any(word in q for word in policy_words):
        return "POLICY"

    return "POLICY"


def policy_assistant(question):
    context = retrieve_policy_context(question)

    if llm is None:
        return {
            "answer": "LLM is not connected. Please add GROQ_API_KEY in environment variables.",
            "retrieved_context": context
        }

    response = llm.invoke([
        SystemMessage(
            content="""
            You are FoodRush Policy Assistant.
            Answer only using the provided context.
            If the answer is not available in context, say it is not available.
            Keep the answer professional and clear.
            """
        ),
        HumanMessage(
            content=f"""
            Context:
            {context}

            Question:
            {question}
            """
        )
    ])

    return {
        "answer": response.content,
        "retrieved_context": context
    }


def complaint_manager(complaint):
    text = complaint.lower()

    if any(word in text for word in ["late", "delay", "hour", "waiting"]):
        category = "DELAY"
        team = "Logistics Team"
        priority = "HIGH"

    elif any(word in text for word in ["wrong", "incorrect", "instead", "different"]):
        category = "WRONG_ORDER"
        team = "Restaurant Team"
        priority = "MEDIUM"

    elif any(word in text for word in ["refund", "money", "payment", "charged"]):
        category = "REFUND"
        team = "Finance Team"
        priority = "MEDIUM"

    elif any(word in text for word in ["cold", "bad", "spoiled", "quality"]):
        category = "FOOD_QUALITY"
        team = "Quality Team"
        priority = "HIGH"

    else:
        category = "GENERAL_COMPLAINT"
        team = "Support Team"
        priority = "MEDIUM"

    if llm is None:
        customer_response = "We are sorry for the inconvenience. Our team will review this issue and update you shortly."
    else:
        response = llm.invoke([
            SystemMessage(
                content="""
                You are FoodRush customer support manager.
                Write an empathetic customer response under 50 words.
                Do not overpromise.
                """
            ),
            HumanMessage(
                content=f"""
                Complaint:
                {complaint}

                Category:
                {category}

                Team:
                {team}

                Priority:
                {priority}
                """
            )
        ])

        customer_response = response.content

    return {
        "category": category,
        "team": team,
        "priority": priority,
        "customer_response": customer_response
    }


def operations_agent(question):
    q = question.lower()
    temp = extract_temperature(question)

    if "peak" in q or "split" in q:
        return peak_time_rider_plan(temp=temp)

    if temp and temp >= 35:
        return hot_weather_plan(temp=temp)

    if "rider" in q or "riders" in q or "driver" in q or "drivers" in q:
        return daily_rider_plan(temp=temp)

    if "order" in q or "orders" in q:
        return {
            "city": FOODRUSH_OPS_DATA["city"],
            "expected_orders_today": FOODRUSH_OPS_DATA["expected_orders_today"],
            "note": "This is the default planning assumption used by the FoodRush AI platform."
        }

    return daily_rider_plan(temp=temp)


def executive_dashboard():
    return {
        "city": FOODRUSH_OPS_DATA["city"],
        "expected_orders_today": FOODRUSH_OPS_DATA["expected_orders_today"],
        "daily_rider_plan": daily_rider_plan(),
        "peak_time_plan": peak_time_rider_plan(),
        "promotion": "10% off lunch and dinner orders",
        "business_insights": [
            "Lunch and evening are the main demand windows.",
            "Peak staffing should be planned separately from daily rider count.",
            "ETA should be adjusted during hot weather or high-demand hours."
        ]
    }


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def home():
    return {
        "message": "FoodRush AI Platform is live.",
        "author": "Huzefa",
        "modules": [
            "Policy Assistant",
            "Operations Agent",
            "Complaint Manager",
            "Executive Dashboard"
        ],
        "sample_endpoint": "/ask"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "groq_connected": bool(GROQ_API_KEY)
    }


@app.post("/ask")
def ask_foodrush(request: QuestionRequest):
    question = request.question
    category = route_query(question)

    if category == "POLICY":
        result = policy_assistant(question)

    elif category == "OPERATIONS":
        result = operations_agent(question)

    elif category == "COMPLAINT":
        result = complaint_manager(question)

    elif category == "DASHBOARD":
        result = executive_dashboard()

    else:
        result = {
            "message": "Sorry, I could not understand the request."
        }

    return {
        "query": question,
        "routed_to": category,
        "result": result
    }
