# SWYTCH: Agentic Career Coach Implementation Plan

**GitHub Issue:** #38  
**Status:** Initial Plan — Open to Team Feedback

## 1. What Are We Trying to Build?

Our project focuses on predicting job satisfaction based on person-job fit. Specifically, we're exploring whether understanding someone's work values and how well those values align with their occupation can help us predict job satisfaction better than demographic information alone.

For the application, the idea is to take the machine learning work we've been doing and turn it into something people can actually interact with.

Instead of only showing our models and results in a presentation, we could create a SWYTCH platform where users complete a short assessment, receive a job satisfaction prediction, and explore what their results mean.

We could then build on that experience by adding an AI career coach that helps users understand their work values, ask questions, and think through career-related decisions.

The goal isn't to build another generic career advice chatbot. We want the experience to connect directly to our research on person-job fit.

## 2. What Would the User Experience Look Like?

Here's the general flow we're thinking of:

1. **Complete an assessment:** Users answer questions about their background, occupation, and work preferences. The exact questions would depend on the features our final model uses.
2. **Explore work values:** If our model supports it, users identify which aspects of a job matter most to them, such as independence, stability, or advancement.
3. **Get a prediction:** The application processes their responses using our trained model and returns a job satisfaction prediction.
4. **Understand the results:** Users can see what the prediction means and explore how person-job fit relates to the outcome.
5. **Talk to the career coach:** Users can ask follow-up questions about their results, work values, and possible career considerations.

We also discussed including a Model Insights section where users can see how our models performed and learn more about the research behind the predictions.

## 3. Main Features We're Considering

### Work Values Assessment

This would be the starting point for users.

We could break the assessment into smaller sections so users aren't overwhelmed by a long form. Depending on our final model, these sections might include background information, occupation details, and work values.

One thing we'll need to confirm is whether the questions we want to ask match the actual features used to train our models.

### Person-Job Fit Results

After completing the assessment, users would receive a prediction about their likelihood of being satisfied at work.

If we have compatible models available, we could also compare a demographic baseline prediction with a model that includes person-job fit features.

This would help us demonstrate the main question behind our project: does including person-job fit improve our ability to predict job satisfaction?

We should also explain that predictions are estimates based on survey data, not guarantees about someone's career.

### Model Insights

This section would give users a look at the research behind the application.

We could include model performance metrics, comparisons between approaches, and some of the main findings from our analysis.

This would also be useful during our final presentation because we could show both the application and the machine learning work supporting it.

### AI Career Coach

This is the main stretch feature we're exploring for Issue #38.

The idea is to give users a way to ask questions about their assessment results instead of leaving them with only a prediction.

For example, someone might ask:

- "What does my result tell me about my current job?"
- "How could my work values affect my job satisfaction?"
- "What should I consider when looking for a new role?"
- "Can you explain why person-job fit matters?"

The coach could use the user's assessment results and information from our project to provide explanations and help them think through possible next steps.

We would need to make sure it doesn't present general career advice as something our model has scientifically proven.

### Settings and Personalization

We also considered allowing users to customize the appearance of the platform.

For example, they could choose between light and dark mode or select from a few different color themes.

This isn't necessary for the first working version, but it could make the application more accessible and enjoyable to use if we have enough time.

## 4. How Would the Agentic Career Coach Work?

Rather than building a chatbot that only responds with general career advice, we could design the coach to work with information from our actual application.

Here's a possible workflow:

**Step 1: Understand the user's question**

The coach identifies what the user wants help with, such as understanding their prediction, exploring work values, or discussing career options.

**Step 2: Check what information is available**

Depending on the question, the coach could use the user's assessment responses, their model prediction, or approved information about our project.

**Step 3: Use the appropriate tool or information**

If the question requires a prediction, the coach should use our trained model rather than generate a prediction on its own.

If the question is about our research, it could reference documented findings and model limitations.

**Step 4: Explain the results**

The coach responds in language that's easy to understand and explains how the information relates to the user's question.

**Step 5: Continue the conversation**

The user can ask follow-up questions or provide more information. The coach could then adjust its response based on the new context.

For the first version, we could start with a simpler conversational assistant that explains assessment results. More advanced tool use could come later if the team has time.

## 5. Possible Tools and Technologies

Since most of our project work is already in Python, it would make sense to consider tools that work well with our existing models.

| Component | Possible Approach |
|---|---|
| User interface | Streamlit |
| Predictions | Our trained Python/scikit-learn models |
| Occupational information | O*NET data already used in our project |
| AI career coach | An LLM connected to approved project information and prediction tools |
| UI sketches | Figma |
| Deployment | A shareable demo, depending on team preference |

These are suggestions rather than final decisions. We would still need to discuss which tools are realistic for the team and the time we have left.

## 6. Step-by-Step Plan for Building It

### Phase 1: Figure Out What We Can Build With Our Current Models

Before designing the assessment, we need to understand what our models can actually support.

- Review the models we've trained so far.
- Decide which model would be best for the demo.
- Identify the input features it requires.
- Confirm whether we have usable person-job fit features.
- Determine what predictions and comparisons we can reliably display.

**Goal:** Know exactly what information the application needs and what results it can provide.

### Phase 2: Sketch the Application

Once we understand the model requirements, we can plan the user experience.

- Sketch the assessment and results pages.
- Decide how users will move between sections.
- Include a space for model insights.
- Sketch the AI career coach interface.
- Consider accessibility and optional theme settings.

**Goal:** Have a visual idea of the platform before building it.

### Phase 3: Build a Basic Working Demo

We can start with the simplest version that demonstrates our research.

- Create an assessment form using the selected model's actual inputs.
- Connect the form to our prediction pipeline.
- Display the predicted result.
- Add explanations and model performance information.
- Test the form using sample inputs.

**Goal:** Have a working application that demonstrates our machine learning work, even without the AI coach.

### Phase 4: Add the Career Coach

Once the prediction feature works, we can build the conversational component.

- Define what types of questions the coach should handle.
- Decide what assessment information it can access.
- Connect it to approved project information and model tools.
- Build a chat interface.
- Test whether its explanations are accurate and relevant.
- Make sure it acknowledges when it doesn't have enough information.

**Goal:** Give users a way to explore their results through conversation.

### Phase 5: Test and Prepare for the Final Demo

Before presenting the application, we should make sure everything works as expected.

- Test the assessment and prediction flow.
- Check that the coach uses actual model outputs.
- Review the interface for usability.
- Document any limitations or unfinished features.
- Prepare a short walkthrough for the final presentation.

**Goal:** Have a demo we can confidently explain and show to our challenge advisors.

## 7. What Should We Prioritize?

Because we're working within a limited timeline, I think we should focus on getting the main prediction experience working before adding too many features.

**First priority:**
- Assessment form
- Working model prediction
- Results explanation
- Model Insights

**Next priority, if feasible:**
- AI career coach
- Model-aware conversational responses

**Additional features, if time allows:**
- Customizable themes
- More interactive work-value comparisons
- Expanded occupation exploration

The AI coach is the focus of this planning issue, but it doesn't have to be the first feature we implement. It makes more sense to connect it to a working prediction system.

## 8. Questions We Still Need to Discuss

Before moving into development, there are a few things the team would need to agree on:

1. Which model are we planning to use for the application?
2. Can users answer the questions required by that model?
3. How are we calculating person-job fit, and is that feature ready?
4. Should we show a single prediction or compare baseline and fit-based models?
5. How advanced do we want the AI coach to be?
6. Which tools would be easiest for us to work with?
7. How much time can we realistically dedicate to building and testing the application?

## 9. Optional UI Sketches

I created an interactive prototype in Figma Make to show what the proposed SWYTCH platform could look like and how users would interact with it.

**Prototype Name:** SWYTCH Career Assessment Platform

The prototype includes six pages:
- Work Values & Person-Job Fit Assessment
- Person-Job Fit Results
- Model Insights
- AI Career Coach
- About SWYTCH
- Settings and Theme Customization

Users can complete the assessment using their own information, review their responses, and explore the proposed results interface. I also included five customizable themes (Light, Dark, Ocean, Forest, and Sunset) so users can personalize their experience.

The design follows a professional, gender-neutral style, with an emphasis on making person-job fit and job satisfaction predictions easier to understand.

For now, the prediction results, alignment scores, and model performance metrics are illustrative placeholders. The prototype isn't connected to our trained machine learning models yet.

The goal is to give our team a visual starting point and help us decide which features we could realistically implement.

**Figma Prototype:** [SWYTCH Career Assessment Platform](https://www.figma.com/make/1T18sPEa6gbJWwV9E2b2z2/SWYTCH-Career-Assessment-Platform?t=DqIz9QJQEhrzWmOb-1)

---

*This is an initial proposal for the team to review. The final design and implementation will depend on our model results, available time, and the direction we agree on as a team.*