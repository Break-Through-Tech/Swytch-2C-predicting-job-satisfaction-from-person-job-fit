---

> ## Challenge Advisor: Update & Finalize Your Project Overview
>
> > 💡 **These grey text instructions are just for you, the team's Challenge Advisor; please delete them once you have completed the steps below.**
>
> We've pre-populated this Challenge Project Overview page — which is what will be shared with your Break Through Tech student team in August — using the details from your submission form. You should have received an email inviting you to join this repo as a Collaborator, enabling you to add files and make edits.
> 
> In order for your project to be finalized and assigned to a team, please:
> 1. **Review all sections below** and update or expand any content as needed, making sure to address the SME Feedback in the section immediately below. Look for square brackets to find the places below that require additional inputs from you (e.g., "About [Company / Org Name]").
> 2. **Add your dataset** to the [data folder](data) in this repo.
> 3. **Close the Issue assigned to you in this repo** to let us know that you have made your edits and the overview page is ready for final review. You can do this by going to the _Issues_ tab in the top left section of the menu above, add a comment that says "CA review complete", and click the button to Close the Issue. 
>
> If you're unfamiliar with how to edit a page like this in GitHub, check out [this tutorial](https://ubc-lib-geo.github.io/gis-workshop-waml-template/content/handson/edit-readme.html) for a quick overview (start with step 2 and only edit this page), and [this guide](https://ubc-lib-geo.github.io/gis-workshop-waml-template/content/markdown.html) on how to use Markdown to compose text.
>
>
> ❌ Remember that this is a public repo. Do NOT include: Proprietary data, PII, API keys, credentials, or anything confidential.

---

## 📋 BTT Internal Evaluation Notes
*(This section is for BTT staff and CAs only — remove before sharing with students)*

### Technical Vetting
| Check | Status | Notes |
| :--- | :--- | :--- |
| Python Compatibility | 🟢 | Stack is fully compatible with standard libraries (pandas, scikit-learn, keras). No complex infrastructure required. |
| Data Readiness | 🟡 | Merging GSS with O*NET requires non-trivial data cleaning and key-matching, which may consume 3-4 weeks of the project timeline. |
| Resource Check | 🟢 | Dataset size is well within Google Colab free-tier limits. No proprietary hardware or API keys required. |

### Internal Scores
- **Student Fit Score:** 8/10
- **Technical Depth Score:** 7/10
- **Overall Recommendation:** REVISE

### Advisor Feedback Draft
This project offers a compelling real-world application of matching algorithms. To ensure success, I recommend two adjustments: first, prioritize interpretable models like Random Forest/XGBoost over Keras to better satisfy the 'explainability' requirement; second, enforce a strict pre-processed dataset snapshot for students to mitigate the data-cleaning bottleneck. I look forward to reviewing your updated milestone plan.

---

# Predicting Job Satisfaction from Person-Job Fit

**Company / Org:** Swytch  
**Challenge Advisor:** Julie Young, julie@swytch.careers  
**Program:** Break Through Tech AI Studio - Fall 2026  

---

## 🏢 About Swytch
Swytch is a career-tech organization dedicated to optimizing professional alignment by focusing on core work values rather than traditional job titles. Their team aims to leverage data science to improve job satisfaction outcomes by effectively matching individuals with roles that provide what they truly need.

---

## 🎯 The Challenge
### Project Summary
This project involves building a machine learning pipeline that integrates General Social Survey (GSS) data with the O*NET occupational database to predict employee job satisfaction. By engineering features that capture the "person-job fit" through matching personal values to occupational offerings, the team will evaluate how these variables influence satisfaction compared to background factors using algorithms like logistic regression, KNN, and tree-based models. The ultimate goal is to provide empirical evidence supporting Swytch's mission that value-based matching yields superior career outcomes.

### Success Criteria
A working pipeline that links the survey data to occupational profiles. Models that predict job satisfaction, with a clear read on how much the fit features improve prediction over background factors alone (reported with standard measures like AUC, plus confidence intervals). A comparison of fit-scoring methods showing which ones actually help. An honest writeup of how big the effect is and where the limits are.

### Project Milestones
Use these milestones to guide your work. Your team will create a GitHub Projects board to track tasks within each milestone.
| Month | Milestone | Key Activities |
|-------|-----------|----------------|
| **September** | Data Exploration & Preprocessing | Conduct EDA on GSS and O*NET datasets, perform cross-dataset key-matching, and establish cleaning protocols for missing values/outliers. |
| **October** | Feature Engineering & Baseline Modeling | Develop "person-job fit" metrics, perform feature selection, and deploy baseline logistic regression and KNN models. |
| **November** | Model Optimization & Evaluation | Execute iterative hyperparameter tuning, implement tree-based models and Keras neural networks, and perform rigorous cross-validation. |
| **December** | Insights, Deliverables & Presentation | Synthesize business recommendations, document model limitations and effect sizes, and package the final technical report. |

> **Note for the team:** Please create a GitHub Projects board in this repository to break these milestones into weekly tasks. Go to the **Projects** tab → **New project** → Choose **Board** → Add columns for each month.

---

## 📊 Dataset
**Name and Source:** General Social Survey (GSS) & O*NET Database  
**Format:** CSV / TSV  
**Size:** under 1gb  
**Location:** Provided via internal project repository and documentation.  

### Key Details
- National survey data on job satisfaction (General Social Survey) and the O*NET database (Numerical/Quantitative and Categorical). Data is in CSV/TSV format and requires some cleaning/preprocessing.
- Requires normalization of survey responses and O*NET descriptors to ensure consistent mapping between personal values and specific occupational attributes.

---

## 🛠️ Suggested Approach
**ML Problem Type:** Classification / Regression  
**Recommended Libraries:**
- Feature engineering
- logistic regression
- tree-based models
- k-nearest neighbors
- Keras neural network
**Evaluation Metrics:** AUC (Area Under the Curve), Confidence Intervals, and feature importance rankings comparing fit-based metrics against demographic baselines.

---

## 📚 Resources to Get Started
The following resources will help your team understand the problem space and potential technical approaches for this project:
**Background Reading:**
- Overview of Person-Job Fit theory and the O*NET occupational classification structure.
**Technical Tutorials:**
- Documentation on scikit-learn preprocessing pipelines and Keras regression architectures.
**Code Examples:**
- Starter notebooks demonstrating GSS/O*NET data merging techniques and baseline model implementations.

---

## 🤝 How We'll Work Together
**Check-ins:** During our biweekly 60-min AI Studio Lab Section meeting block (2nd and 4th week of every month)  
**Communication:** Email and Slack workspace channels  
**Response time:** 24-48 business hours  
**Recommended Tools:**
- **Coding:** Google Colab Free Tier  
- **Collaboration:** GitHub, Notion  
- **Virtual Meetings:** Zoom, Google Meet  

---

## 🚀 Getting Started
1. **Review this overview document** and note any questions for our first meeting.
2. **Begin reviewing the dataset** using the link provided in the Dataset section.
3. **Read the GitHub Projects documentation** [here](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects).

I'm excited to work with you!

---

## ❓ Questions?
Please bring any questions to our first meeting during the week of August 24th (Break Through Tech's Bridge to Studio - Session B).
