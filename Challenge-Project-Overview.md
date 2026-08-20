# Predicting Job Satisfaction from Person-Job Fit

**Company / Org:** Swytch  
**Challenge Advisor:** James Thompson, [jimt@swytch.careers]  
**Program:** Break Through Tech AI Studio - Fall 2026  

---

## 🏢 About Swytch
Swytch is a career-tech organization dedicated to optimizing professional alignment by focusing on core work values rather than traditional job titles. Their team aims to leverage data science to improve job satisfaction outcomes by effectively matching individuals with roles that provide what they truly need.

---

## 🎯 The Challenge
### Project Summary
In this project, you will use national survey data on job satisfaction (e.g., the General Social Survey) together with the O*NET database of what occupations involve, and machine learning methods (feature engineering, logistic regression, tree-based models, k-nearest neighbors, and a Keras neural network), to predict whether someone is satisfied at work based on how well their personal work values match what their job actually offers. This tests a core idea behind SWYTCH: that matching people on what they value, not just on job titles, leads to better outcomes.

### Success Criteria
A working pipeline that links the survey data to occupational profiles. Models that predict job satisfaction, with a clear read on how much the fit features improve prediction over background factors alone (reported with standard measures like AUC, plus confidence intervals). A comparison of fit-scoring methods showing which ones actually help. And an honest writeup of how big the effect is and where the limits are. The scoring recipe stays in-house; students report findings only.

### Stretch Goals

- Free option: break the results out by industry or demographic group to see where the value-satisfaction link is strongest and weakest, or test how stable the findings are across survey years.
- Optional API-based add-on (TBD, only if API access is later funded): have the model generate plain-language explanations of a person's fit, or a question-answering assistant over the survey codebook and O*NET docs.

### Project Milestones
Use these milestones to guide your work. Your team will create a GitHub Projects board to track tasks within each milestone.

| Month | Milestone | Key Activities |
|---|---|---|
| September | Data Linkage & Exploration | Match the survey's occupation codes to O*NET. Combine each person's work values and job satisfaction with their occupation's profile. Explore the data. |
| October | Baseline Models & Evaluation Setup | Build simple baseline models using only background factors (income, hours, demographics). Set up a fair way to measure results when the satisfied and unsatisfied groups are different sizes. |
| November | Fit Features & Model Comparison | Add the "fit" features. Track A measures how much they improve the prediction; Track B compares different ways of scoring fit. Add a Keras neural network for comparison. |

> **Note for the team:** Please create a GitHub Projects board in this repository to break these milestones into weekly tasks. Go to the **Projects** tab → **New project** → Choose **Board** → Add columns for each month.

---

## 📊 Dataset
**Name and Source:** General Social Survey (GSS) & O*NET Database  
**Format:** SPSS (can read with pyreadstat library)
**Size:** under 1gb  
**Location:** https://gss.norc.org/get-the-data.html, https://www.onetcenter.org/database.html, https://www.onetcenter.org/crosswalks.html)

**Name and Source:** The American Job Quality Study: 2025  
**Format:** CSV / TSV  
**Size:** under 1gb  
**Location:** (https://www.gallup.com/analytics/691241/american-job-quality-study.aspx)

### Key Details
- [Brief description of what's in the data]
- [Any known limitations or preprocessing needed]
- [Link to data dictionary or documentation, if available]
  
---

## 🛠️ Suggested Approach

**ML Problem Type:** Classification,Regression,Deep Learning / Neural Networks

**Recommended Libraries:**
- [e.g., pandas, scikit-learn, TensorFlow, Hugging Face]

**Evaluation Metrics:**
- [e.g., Accuracy, Precision/Recall, RMSE, BLEU score]

---

## 📚 Resources to Get Started

The following resources will help your team understand the problem space and potential technical approaches for this project:

**Background Reading:**
- [e.g., Link to an article or blog post about the problem domain]
- [e.g., Link to an industry report or case study]

**Technical Tutorials:**
- [e.g., Link to a free tutorial on the ML technique(s) involved]
- [e.g., Link to documentation for a key library or tool]

**Code Examples:**
- [e.g., Link to a relevant GitHub repo]
- [e.g., Link to a sample implementation or starter code]

**Other:**
- [Links to any additional resources — e.g., papers, videos, podcasts, etc.]

*Feel free to explore beyond these, and share anything interesting you find with me!*

---

## 🤝 How We'll Work Together

**Official check-ins:** During our biweekly 45-minute AI Studio Lab Section meeting block (2nd and 4th week of every month)

 **Other ways to reach out to me with questions:** 
* [e.g., Your team's channel within Break Through Tech’s Discord space]
* [e.g., Email; please copy your teammates and AI Studio Coach]
* [e.g., Request a team check-in on Zoom]
* [Note: I will aim to respond within 48 hours. Please reach out to your AI Studio Coach with urgent questions.]

> 💡 **Challenge Advisor: Please update the above based on your availability and preference. If you are not able to answer questions or meet with fellows outside of the biweekly Lab Section check-ins, simply write in "N/A (only available during the official check-in times)"**

**Recommended free coding / collaboration tools**
* […]
* […]

---

## 🚀 Getting Started

1. **Review this overview document** and note any questions for our first meeting
2. **Begin reviewing the dataset** using the link above
3. **Read the GitHub Projects documentation** [here](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)

I’m excited to work with you!

---

## ❓ Questions?

Please bring any questions to our first meeting during the week of August 24th (Break Through Tech’s Bridge to Studio - Session C). 
