# Day 02 — Prompt and Context Experiment Results

**Project:** Local GenAI Employee Assistant  
**Configured model:** `qwen2.5:3b` (confirm this matches the model used during the run)  
**Access method:** Local Ollama Python SDK  
**Interface:** Streamlit

## Version definitions

| Version | Configuration |
|---|---|
| Version A — Baseline | User question only |
| Version B — Improved Instructions | System instructions + user question |
| Version C — Instructions + Context | System instructions + question and any context supplied in the app |

## Summary of observed behavior

| Test | Version A | Version B | Version C |
|---|---|---|---|
| 1. Annual leave vs sick leave | Gave a detailed general explanation | Gave a shorter explanation with more specific usage examples | Refused to answer because the supplied context did not contain leave definitions |
| 2. Professional leave request | Rewrote the request in one sentence | Rewrote it with a placeholder date | Asked for more details instead of completing the rewrite |
| 3. Five days of annual leave | Said the answer depends on company policy, but included an unsupported suggestion that five days may not need special clearance | Said to check the handbook or ask HR/manager | Referred to different policy facts (24 days annually, 16 already taken, 42 days remaining), not the assignment context |
| 4. Parental leave policy | Incorrectly referred to Alibaba Group as though it were the user’s company | Said the company policy was not provided and referred to HR | Said it did not have the company-specific policy and referred to HR |
| 5. Travel approval | Gave a lengthy list of possible approvers and contexts | Gave a shorter generic answer and recommended checking policy/HR | Gave a similar generic answer, despite no relevant travel-policy context |

> **Important Test 3 issue:** The assignment context is: “Employees receive 20 days of annual leave per calendar year. Leave requests of more than three consecutive days require manager approval.” The recorded Version C response instead mentions 24 annual days, 16 days already used, and 42 days until year-end. That means the Version C run did not use the intended context for this test. Re-run Test 3 with the exact assignment context before using it as evidence.

> **Interpretation note:** These observations describe the outputs actually recorded in the supplied text. They are not proof that the same behavior will occur on every run.

## Test 1 — Explain the difference between annual leave and sick leave.

### Version A — Baseline

Annual leave and sick leave are two types of time-off policies that employees often have in their employment contracts. They serve different purposes but can be used for various reasons.

Annual Leave: Annual leave, also known as vacation or holiday, is a type of paid time off given to employees by their employers, typically on an annual basis. It is usually accrued over the course of one's employment and is intended to allow workers to take time away from work for personal reasons, such as spending time with family, visiting friends, engaging in hobbies, traveling, or simply relaxing.

Sick Leave: On the other hand, sick leave (or medical leave) refers to a form of paid time off that employees are entitled to when they need to recover from an illness. It is intended for individuals who are not fit to work due to being unwell and therefore cannot perform their job duties normally.

Key differences include:

Purpose: Annual leave is primarily meant for personal use, while sick leave covers periods of sickness or temporary incapacity.

Acquisition Process: Employees typically accrue annual leave over the course of their employment through regular work contributions. Sick leave can also accumulate over time but it might have more stringent eligibility criteria (like a doctor's note) to ensure that employees are genuinely incapacitated.

Usage Conditions: Annual leave is generally used for personal needs, while sick leave allows an employee to take time off when they need medical attention and rest due to illness or injury.

Accrual Rates: The accrual rate for annual leave can vary based on factors like seniority, job role, company policy, etc., whereas sick leave usually has specific rates that are established by the employer.

Employment Status Consideration: In some cases, employees who have been employed for a certain period may be eligible to start accruing annual leave from their first day of employment or soon after starting work, while sick leave eligibility can sometimes depend on factors like length of service, company policy, and specific health conditions.

It's important to note that the details such as policies and procedures regarding these leaves can vary significantly between different companies. Employees should familiarize themselves with the specific terms in their contracts or HR guidelines provided by their employers.

### Version B — Improved Instructions

Annual leave and sick leave are two different types of paid time off from work.

Annual Leave: This type of leave is typically intended for days or periods when an employee does not need to work due to pre-arranged reasons such as personal vacations, weddings, birthdays, holidays, or any other personal commitments that are planned well in advance by the employee. Employers usually offer annual leave based on a fixed number of days per year and often employees must use their annual leave before it expires.

Sick Leave: This type of leave is used when an employee needs to take time off due to illness, health condition, or injury. The primary purpose is for the employee's recovery or medical treatment, not personal reasons. Employers usually have specific guidelines about how and when sick leave can be taken. If the employee does not follow these guidelines strictly (for example, if they don't seek a doctor's appointment or follow their healthcare provider's advice), their absence might not be considered as sick leave.

Both types of leave are often governed by labor laws that specify eligibility requirements, usage limits, and compensation for unused time. However, the intent behind taking each type of leave is different - annual leave is for personal use while sick leave is for maintaining or restoring one's health.

### Version C — Instructions + Context

I don't know

The provided context does not contain information about explaining the difference between annual leave and sick leave.

## Test 2 — Rewrite this leave request professionally: I need leave tomorrow for personal work.

### Version A — Baseline

I am submitting a leave request for tomorrow due to personal matters.

### Version B — Improved Instructions

I require a day of leave on [specific date] for personal reasons.

### Version C — Instructions + Context

I don't know. Please provide me with what details should be included in the leave request.I need you to provide the 

## Test 3 — I want to take five days of annual leave. Does this require manager approval?

### Version A — Baseline

Whether your request for five days of annual leave requires manager approval depends on the specific policies and procedures at your workplace. Generally:

Company Policy: Most companies have their own HR guidelines regarding how much time off can be granted without prior approval, especially for short-term requests like a weekend or bank holiday.

Policy Clarification: It's important to check your company’s employee handbook or speak with your Human Resources department for the most accurate information. Often, five days is considered a "reasonable" amount of leave that doesn't require special clearance from management.

Management Approval (if required): If your workplace has specific policies requiring managerial approval for annual leave requests above certain limits (e.g., more than one day), you should ensure to comply with those guidelines.

If unsure, it’s always best to consult directly with the Human Resources department or your manager. They can provide clear guidance based on your company's practices and any unique requirements that might apply.

### Version B — Improved Instructions

To determine if your request for five days of annual leave requires manager approval, you should check your employee handbook or any company policies related to vacation time. Typically, the decision on whether management needs to approve a request can vary by organization. Some companies may require approval for all leave requests, while others might only need it for specific amounts or types of leave.

If your policy isn't clear about this, you should contact your HR department or manager directly for guidance. They will be able to provide the most accurate and up-to-date information based on your company's procedures.

### Version C — Instructions + Context

Based on the provided context, there is no information about whether taking specific amounts of annual leaves requires manager approval or not. The context only mentions that you had 24 leaves annually and have taken 16 already this year, with 42 days until the end of the year.

Therefore, I dont know if taking five days of annual leave would require manager approval based on the information given.

## Test 4 — What is our company's parental leave policy?

### Version A — Baseline

I'm sorry for the confusion, but as Qwen, an AI assistant created by Alibaba Cloud, I don't have direct access to specific information about Alibaba Group Holding's policies or internal systems since my knowledge cutoff was in 2021. Therefore, I do not have the most up-to-date and detailed information regarding parental leave policy for Alibaba Group.

For accurate and current details on such company-specific policies, you should refer directly to the official Alibaba Group employee handbook, human resources department, or contact their HR support line. They can provide you with the most relevant and specific information about parental leave benefits and other employment policies that are applicable to employees.

### Version B — Improved Instructions

I'm sorry, but I don't have access to specific information about your company's policies as it wasn't provided in the initial context. To find out our company's parental leave policy, you should consult the employee handbook or reach out to HR directly for accurate details.

### Version C — Instructions + Context

I'm sorry, but I don't have access to specific company policies as my knowledgebase doesn't include details about individual companies. To find out our company's parental leave policy, you should check the employee handbook or contact HR directly for accurate information. They will be able to provide the most up-to-date and relevant details regarding parental leave from your organization.

## Test 5 — Who should approve my travel request?

### Version A — Baseline

The person who should approve your travel request depends on the specific context and workplace policies. Here are some common scenarios:

For Employees: In most companies, this decision would be made by your direct supervisor or HR department. They have knowledge about your job responsibilities and can make an informed decision based on your availability and work commitments.

For Students/Students Living in Campus Housing: Your request might go through a housing office or student affairs team that manages accommodation requests for students.

For External Parties (e.g., Contractors, Guests): Approval would likely be given by the person who oversees the project or contract you are working on, possibly your manager or someone in leadership.

Internal Travel: If it is an internal travel request within a company setting, your department head might approve it based on their availability and organizational needs.

Temporary Workers (Freelancers): In some cases, a freelancer's work request would be approved by the person who hired them or someone in charge of their team or project.

It’s important to check with your company's policies specifically regarding travel requests, as these can vary significantly between organizations. If you are unsure about who should approve your request, you might need to consult your HR department or a relevant manager within your organization.

### Version B — Improved Instructions

The person who should approve your travel request depends on your organization's structure and policies. Typically, it could be your supervisor or a manager within your department if you are an employee. For higher-level executives or contractors, the approval might come from upper management or a specific department head. It is best to check with HR or your company's travel policy for clarification on who should approve your request.

### Version C — Instructions + Context

The person who should approve your travel request will depend on your organization's policy and structure. Typically, this could be a supervisor, manager, or HR representative depending on your company hierarchy and policies. It's best to check with your direct supervisor or the HR department for specific guidelines regarding travel approval in your organization.

## Reflections from the recorded outputs

1. **Instructions did not automatically improve every task.** Version B handled the professional rewrite differently from Version A, but used a placeholder date rather than a fully ready-to-send request.
2. **Context use was too restrictive in some runs.** Version C answered “I don’t know” for general knowledge and transformation tasks when it treated supplied context as the only allowed source, even though those tasks did not require internal policy context.
3. **Missing internal knowledge was handled better in B and C.** For parental leave, Versions B and C acknowledged that the company policy was unavailable. Version A made an unsupported company-specific assumption by referring to Alibaba Group.
4. **Ambiguous internal questions remained unresolved.** All three versions lacked the company’s travel approval hierarchy. Versions B and C still offered generic possibilities instead of confidently identifying an approver, which is safer than inventing a definite policy but does not answer the company-specific question.
5. **The context must be controlled during testing.** Version C only provides a fair comparison when it receives the intended context for the relevant test and no unrelated context for tests that have none.

## Recommended retest before submission

For Test 3, clear any previous context and enter exactly this context:

> Employees receive 20 days of annual leave per calendar year. Leave requests of more than three consecutive days require manager approval.

Then ask:

> I want to take five days of annual leave. Does this require manager approval?

For Tests 1, 2, 4, and 5, leave the context box empty unless your app design explicitly separates task instructions from supplied company context. Save the fresh outputs and update this report with the corrected Test 3 response.
