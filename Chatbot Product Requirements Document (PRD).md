

------

# Product Requirements Document (PRD)

##  BrightWave GenAI Telco Agent Assist (AI Chatbot for Billing Support)

------

## 1. Product Overview

**Product Name:** BrightWave (GenAI Telco Agent Assist)
 **Primary Users:** Phone Agents (Customer Support Representatives)
 **Core Purpose:**
 Provide an AI-powered chat assistant that enables agents to quickly generate **clear, customer-ready explanations for billing and payment inquiries**.

**Top-Level Capability Areas:**

- Bill explanation & comparison
- Billing event interpretation (changes, fees, credits, services)
- Standardized response generation
- Configurable formatting and interpretation rules
- Reporting and continuous learning

------

## 2. Feature Hierarchy (Derived from Jira Parent/Child Relationships)

### Epic: **BOE-1868 – BrightWave (GenAI Telco Agent Assist)**

#### 2.1 Core Functional Modules

| Module                   | Jira Epic | Description                                               |
| ------------------------ | --------- | --------------------------------------------------------- |
| Access & Platform        | BOE-1870  | Core assistant functionality, formatting, system behavior |
| General Billing Q&A      | BOE-1871  | High-level bill explanation and comparisons               |
| Bill Change Explanations | BOE-1876  | Detailed breakdown of bill drivers                        |
| Answer Standardization   | BOE-1875  | Structured, consistent messaging                          |

------

## 3. Requirements Table (Numbered)

> **Legend**
>  ✅ = Current (assumed available unless deferred)
>  🟡 = Future / Backlog (Technical Review or not clearly released)

| #    | Requirement                                                  | Category      | Source Tickets | Status |
| ---- | ------------------------------------------------------------ | ------------- | -------------- | ------ |
| 1    | Agents can access AI chatbot for billing inquiries           | Platform      | BOE-1899       | ✅      |
| 2    | System generates customer-ready responses for general bill explanations | Core Function | BOE-1911       | ✅      |
| 3    | System answers general charge-related questions              | Core Function | BOE-1913       | ✅      |
| 4    | System compares bills and explains differences               | Core Function | BOE-1912       | ✅      |
| 5    | System explains bill changes and variations                  | Core Function | BOE-1910       | ✅      |
| 6    | Standardized answer structure across all responses           | UX/Content    | BOE-1903       | ✅      |
| 7    | Responses are customer-friendly and copy/paste ready         | UX/Content    | BOE-1902       | ✅      |
| 8    | Default to most recent bill if none specified                | Logic         | BOE-1905       | ✅      |
| 9    | Interpret month names correctly                              | Logic         | BOE-1904       | ✅      |
| 10   | Standard date formatting                                     | Formatting    | BOE-1906       | ✅      |
| 11   | Standard currency formatting ($XX.XX)                        | Formatting    | BOE-1907       | ✅      |
| 12   | Internet speed represented via plan naming                   | Formatting    | BOE-1908       | ✅      |
| 13   | Voice usage standardized                                     | Formatting    | BOE-1909       | ✅      |
| 14   | Ability to upload new Q&A content                            | Admin         | BOE-1901       | ✅      |
| 15   | Reporting and analytics (questions, gaps, feedback)          | Analytics     | BOE-1900       | ✅      |
| 16   | System learns from unanswered questions                      | AI Capability | BOE-1900       | ✅      |
| 17   | Explain **plan changes** (proration, partial charges/credits) | Bill Changes  | BOE-1924       | ✅      |
| 18   | Explain **rate changes** and discounts                       | Bill Changes  | BOE-1926       | ✅      |
| 19   | Explain **new service additions (LOB)**                      | Bill Changes  | BOE-1927       | ✅      |
| 20   | Explain **service removals (LOB)**                           | Bill Changes  | BOE-1928       | ✅      |
| 21   | Explain **all services disconnection scenario**              | Bill Changes  | BOE-1929       | ✅      |
| 22   | Explain **equipment changes**                                | Bill Changes  | BOE-1930       | ✅      |
| 23   | Explain **equipment returns / non-return fees**              | Bill Changes  | BOE-1931       | ✅      |
| 24   | Explain **past due amounts**                                 | Bill Changes  | BOE-1932       | ✅      |
| 25   | Explain **late fees and conditions**                         | Bill Changes  | BOE-1933       | ✅      |
| 26   | Explain **balance forward / negative balances**              | Bill Changes  | BOE-1934       | ✅      |
| 27   | Explain **end of loyalty credits**                           | Bill Changes  | BOE-1923       | ✅      |
| 28   | Explain **bundle promo removal due to mobile cancellation**  | Bill Changes  | BOE-1922       | ✅      |

------

## 4. Detailed Requirements (Expanded Descriptions)

### 1. Agent Access to AI Assistant

The system must provide agents with an accessible interface to interact with the chatbot for billing-related inquiries. It should be easy to use and integrated into agent workflows.

------

### 2–5. Core Billing Q&A Capabilities

The chatbot must:

- Provide clear bill explanations (Req #2)
- Answer general billing questions (Req #3)
- Compare multiple bills and identify differences (Req #4)
- Explain why bill amounts changed (Req #5)

Responses must be:

- Accurate
- Context-aware
- Customer-ready

------

### 6–7. Response Standardization & Quality

- Responses must follow a **consistent structure** to ensure predictability (#6)
- Language must be **simple, customer-friendly**, and ready for direct copy-paste (#7)

------

### 8–9. Time Interpretation Logic

- If no billing period is specified, default to the **most recent bill** (#8)
- Recognize natural language references to time (e.g., “March bill”) (#9)

------

### 10–13. Formatting Standards

Ensure all responses follow consistent formatting:

- Dates standardized (#10)
- Currency formatted cleanly (#11)
- Internet speed represented meaningfully (#12)
- Voice usage displayed clearly (#13)

------

### 14. Content Management

Product owners must be able to:

- Upload additional Q&A content
- Expand chatbot knowledge over time

------

### 15–16. Reporting & Learning

The system must:

- Track usage, including unanswered questions (#15)
- Provide analytics for improvement
- Support learning loops to improve future responses (#16)

------

## 5. Bill Change Explanation Engine

This is the **core intelligence layer** of the chatbot.

### 17. Plan Changes

Explain:

- Proration
- Partial charges/credits
- Net financial impact

------

### 18. Rate Changes

Explain:

- Base price adjustments
- Discount offsets (partial/full)
- Customer-visible impacts

------

### 19–20. Service Changes (LOB)

- Addition of services → partial charges + bundle impacts (#19)
- Removal of services → credits + bundle change effects (#20)

------

### 21. Full Disconnection

Explain:

- End-state billing
- Final bill logic
- Residual charges

------

### 22–23. Equipment Handling

Explain:

- Equipment additions/removals (#22)
- Returned vs unreturned equipment (#23)
- Associated credits or fees

------

### 24–26. Billing Financial Components

Must explain:

- Past due amounts (#24)
- Late fees and triggers (#25)
- Balance forward and negative balances (#26)

------

### 27. Loyalty Credits

Explain:

- Expiration of credits
- Duration (if available)
- Avoid speculation on cause

------

### 28. Bundle Logic

Explain:

- Loss of promotion when dependencies (e.g., mobile) are removed
- SOC/offer relationships
- Discount attribution changes

------

## 6. Future / Backlog Capabilities

These are inferred as **not fully delivered yet (Technical Review / platform-level items)**:

### Platform Enhancements

- Standardized formatting engine
- Unified answer structure enforcement
- Flexible interpretation logic

### Intelligence Expansion

- Self-learning from unanswered questions
- Smarter contextual understanding

### Operational Improvements

- Reporting dashboards
- Content management workflows

------

## 7. Assumptions

- All **“Funnel” + “Ready for Testing”** items are treated as **current features**
- All **“Technical Review”** items are treated as **future/backlog**
- No explicit deferrals were marked, so backlog inferred from status

------

## 8. Key Value Proposition

The chatbot enables:

- Faster agent response times
- Reduced training burden
- Consistent customer experience
- Improved bill transparency

------

If you want, I can also:

- Map this into a **solution architecture (LLM + data sources + flows)**
- Or generate **user journeys / conversation flows** from these requirements