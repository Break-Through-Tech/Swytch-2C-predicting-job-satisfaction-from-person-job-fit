import { useState } from 'react';
import './Assessment.css';

const steps = [
  'Background',
  'Work Values',
  'Occupation & Fit',
  'Review',
];

const educationOptions = [
  { value: 'high-school', label: 'High school' },
  { value: 'associate', label: 'Associate degree' },
  { value: 'bachelor', label: "Bachelor's degree" },
  { value: 'master', label: "Master's degree" },
  { value: 'doctorate', label: 'Doctoral degree' },
];

const careerStageOptions = [
  {
    value: 'exploring',
    label: 'Exploring / entering workforce',
  },
  { value: 'early', label: 'Early career' },
  { value: 'mid', label: 'Mid-career' },
  {
    value: 'experienced',
    label: 'Experienced professional',
  },
];

const workValueOptions = [
  {
    key: 'autonomy',
    label: 'Autonomy',
    description: 'Freedom to make decisions about your work.',
  },
  {
    key: 'stability',
    label: 'Stability',
    description: 'Having reliable and secure employment.',
  },
  {
    key: 'advancement',
    label: 'Advancement',
    description: 'Opportunities to grow in your career.',
  },
  {
    key: 'recognition',
    label: 'Recognition',
    description: 'Feeling appreciated for your contributions.',
  },
  {
    key: 'workLifeBalance',
    label: 'Work-life balance',
    description: 'Having time for life outside of work.',
  },
];

// PROVISIONAL OCCUPATION DATA
// Replace this array with confirmed supported occupations
// from the backend during model integration.

const occupationOptions = [
  'Accountant',
  'Business Analyst',
  'Cybersecurity Intern',
  'Data Analyst',
  'Data Scientist',
  'Financial Analyst',
  'Graphic Designer',
  'Human Resources Specialist',
  'Information Security Analyst',
  'IT Support Specialist',
  'Marketing Specialist',
  'Mechanical Engineer',
  'Network Administrator',
  'Project Manager',
  'Registered Nurse',
  'Software Developer',
  'Systems Analyst',
  'Teacher',
  'UX Designer',
];

export default function Assessment() {
  const [currentStep, setCurrentStep] = useState(0);

  const [education, setEducation] = useState('');
  const [careerStage, setCareerStage] = useState('');
  const [experience, setExperience] = useState('');

  const [workValues, setWorkValues] = useState<
    Record<string, number>
  >({});

  const [occupation, setOccupation] = useState('');
  const [occupationSearch, setOccupationSearch] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const [validationMessage, setValidationMessage] = useState('');

  // OCCUPATION SEARCH

  const searchTerm = occupationSearch.trim().toLowerCase();

  const filteredOccupations = occupationOptions.filter(
    (option) =>
      option.toLowerCase().includes(searchTerm)
  );

  const hasOccupationMatch =
    occupation !== '' &&
    occupationOptions.includes(occupation);

  // WORK VALUES VALIDATION

  const allWorkValuesCompleted = workValueOptions.every(
    (value) =>
      workValues[value.key] >= 1 &&
      workValues[value.key] <= 5
  );

  const completedWorkValues = workValueOptions.filter(
    (value) => workValues[value.key] !== undefined
  ).length;

  // REVIEW LABELS

  const educationLabel =
    educationOptions.find(
      (option) => option.value === education
    )?.label || '';

  const careerStageLabel =
    careerStageOptions.find(
      (option) => option.value === careerStage
    )?.label || '';

  const hasBackgroundInformation = Boolean(
    educationLabel || careerStageLabel || experience
  );

  // NAVIGATION

  const nextStep = () => {
    setValidationMessage('');

    if (currentStep === 1 && !allWorkValuesCompleted) {
      setValidationMessage(
        'Please rate each work value before continuing.'
      );
      return;
    }

    if (currentStep === 2 && !hasOccupationMatch) {
      setValidationMessage(
        'Please select a matching occupation before continuing.'
      );
      return;
    }

    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const previousStep = () => {
    setValidationMessage('');
    setSubmitted(false);

    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const editStep = (step: number) => {
    setValidationMessage('');
    setSubmitted(false);
    setCurrentStep(step);
  };

  // OCCUPATION HANDLERS

  const handleOccupationSearch = (value: string) => {
    setOccupationSearch(value);
    setOccupation('');
    setValidationMessage('');
    setSubmitted(false);
  };

  const selectOccupation = (value: string) => {
    setOccupation(value);
    setOccupationSearch(value);
    setValidationMessage('');
    setSubmitted(false);
  };

  const clearOccupation = () => {
    setOccupation('');
    setOccupationSearch('');
    setValidationMessage('');
    setSubmitted(false);
  };

  // TEMPORARY SUBMISSION
  // Replace with the prediction API integration when ready.

  const submitAssessment = () => {
    setValidationMessage('');

    if (!allWorkValuesCompleted) {
      setCurrentStep(1);
      setValidationMessage(
        'Please complete all work value ratings.'
      );
      return;
    }

    if (!hasOccupationMatch) {
      setCurrentStep(2);
      setValidationMessage(
        'Please select a matching occupation.'
      );
      return;
    }

    setSubmitted(true);
  };

  return (
    <section className="assessment-page">

      {/* ASSESSMENT HEADER */}

      <div className="assessment-header">
        <div className="assessment-header-top">
          <span className="assessment-eyebrow">
            PERSON–JOB FIT ASSESSMENT
          </span>

          <span className="provisional-badge">
            Provisional fields
          </span>
        </div>

        <h1>Tell Us About You and Your Work Values</h1>

        <p>
          A provisional assessment flow for reviewing how future
          model inputs could be collected.
        </p>
      </div>

      <div className="assessment-notice" role="note">
        <strong>Questions and answer choices are not final.</strong>
        {' '}These fields are placeholders for experience review and
        are not yet mapped to the trained model or confirmed dataset inputs.
      </div>

      <div className="assessment-card">

        {/* PROGRESS INDICATOR */}

        <div className="assessment-progress">
          {steps.map((step, index) => (
            <div
              className={`progress-step ${
                index === currentStep ? 'current' : ''
              } ${index < currentStep ? 'completed' : ''}`}
              key={step}
              aria-current={
                index === currentStep ? 'step' : undefined
              }
            >
              <div className="progress-number">
                {index < currentStep ? '✓' : index + 1}
              </div>

              <span>{step}</span>
            </div>
          ))}
        </div>

        <div className="assessment-body">

          {/* ========================================
              STEP 1: BACKGROUND
              ======================================== */}

          {currentStep === 0 && (
            <>
              <div className="assessment-section-heading">
                <span className="section-number">01</span>

                <div>
                  <h2>First, a little about your background</h2>

                  <p>
                    This context helps the research team understand
                    broad participant patterns.
                  </p>
                </div>
              </div>

              <div className="assessment-fields">
                <div className="assessment-field">
                  <label htmlFor="education">
                    Highest level of education
                    <span> (optional)</span>
                  </label>

                  <select
                    id="education"
                    value={education}
                    onChange={(event) =>
                      setEducation(event.target.value)
                    }
                  >
                    <option value="">
                      Select your education level
                    </option>

                    {educationOptions.map((option) => (
                      <option
                        key={option.value}
                        value={option.value}
                      >
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="assessment-field">
                  <label htmlFor="career-stage">
                    Current career stage
                    <span> (optional)</span>
                  </label>

                  <select
                    id="career-stage"
                    value={careerStage}
                    onChange={(event) =>
                      setCareerStage(event.target.value)
                    }
                  >
                    <option value="">
                      Select your career stage
                    </option>

                    {careerStageOptions.map((option) => (
                      <option
                        key={option.value}
                        value={option.value}
                      >
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="assessment-field experience-field">
                <label>
                  Years of work experience
                  <span> (optional)</span>
                </label>

                <div
                  className="experience-options"
                  role="group"
                  aria-label="Years of work experience"
                >
                  {[
                    'Less than 1',
                    '1–3 years',
                    '4–7 years',
                    '8–15 years',
                    '16+ years',
                  ].map((option) => (
                    <button
                      key={option}
                      type="button"
                      aria-pressed={experience === option}
                      className={
                        experience === option ? 'selected' : ''
                      }
                      onClick={() => setExperience(option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* ========================================
              STEP 2: WORK VALUES
              ======================================== */}

          {currentStep === 1 && (
            <>
              <div className="assessment-section-heading">
                <span className="section-number">02</span>

                <div>
                  <h2>What matters most to you at work?</h2>

                  <p>
                    Rate how important each work value is to you.
                    These categories are provisional.
                  </p>
                </div>
              </div>

              <div className="work-values-guide">
                <span>1 = Lower importance</span>
                <span>5 = Higher importance</span>
              </div>

              <div className="work-values-list">
                {workValueOptions.map((value) => (
                  <div
                    className="work-value-row"
                    key={value.key}
                  >
                    <div className="work-value-info">
                      <h3>{value.label}</h3>
                      <p>{value.description}</p>
                    </div>

                    <div
                      className="work-value-rating"
                      role="group"
                      aria-label={`${value.label} importance`}
                    >
                      {[1, 2, 3, 4, 5].map((rating) => (
                        <button
                          key={rating}
                          type="button"
                          className={
                            workValues[value.key] === rating
                              ? 'selected'
                              : ''
                          }
                          aria-pressed={
                            workValues[value.key] === rating
                          }
                          aria-label={`${value.label}: ${rating} out of 5`}
                          onClick={() => {
                            setWorkValues((previous) => ({
                              ...previous,
                              [value.key]: rating,
                            }));

                            setValidationMessage('');
                            setSubmitted(false);
                          }}
                        >
                          {rating}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="work-values-completion">
                <span>
                  {completedWorkValues} of {workValueOptions.length}
                  {' '}values rated
                </span>

                <div className="completion-track">
                  <div
                    className="completion-fill"
                    style={{
                      width: `${
                        (completedWorkValues /
                          workValueOptions.length) * 100
                      }%`,
                    }}
                  />
                </div>
              </div>
            </>
          )}

          {/* ========================================
              STEP 3: OCCUPATION & FIT
              ======================================== */}

          {currentStep === 2 && (
            <>
              <div className="assessment-section-heading">
                <span className="section-number">03</span>

                <div>
                  <h2>Tell us about your occupation</h2>

                  <p>
                    Identify your current or intended occupation
                    to provide context for your person–job fit
                    assessment.
                  </p>
                </div>
              </div>

              <div className="assessment-field">
                <label htmlFor="occupation-search">
                  Current or intended occupation
                  <span className="required-label"> *</span>
                </label>

                <div className="occupation-search-wrapper">
                  <svg
                    className="occupation-search-icon"
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    aria-hidden="true"
                  >
                    <circle cx="11" cy="11" r="7" />
                    <path d="m16 16 5 5" />
                  </svg>

                  <input
                    id="occupation-search"
                    type="text"
                    className="occupation-search"
                    placeholder="Enter your job title..."
                    value={occupationSearch}
                    autoComplete="off"
                    aria-required="true"
                    onChange={(event) =>
                      handleOccupationSearch(event.target.value)
                    }
                  />

                  {occupationSearch && (
                    <button
                      type="button"
                      className="clear-search"
                      aria-label="Clear occupation search"
                      onClick={clearOccupation}
                    >
                      ×
                    </button>
                  )}
                </div>

                {/* EMPTY SEARCH STATE */}

                {!searchTerm && (
                  <p className="occupation-hint">
                    Start typing your job title to find a matching
                    occupation.
                  </p>
                )}

                {/* MATCHING OCCUPATIONS */}

                {searchTerm &&
                  !hasOccupationMatch &&
                  filteredOccupations.length > 0 && (
                    <div className="occupation-suggestions">
                      <div className="suggestions-heading">
                        Matching occupations
                      </div>

                      <div className="occupation-list">
                        {filteredOccupations.map((option) => (
                          <button
                            key={option}
                            type="button"
                            className="occupation-option"
                            onClick={() =>
                              selectOccupation(option)
                            }
                          >
                            <span>{option}</span>

                            <span
                              className="suggestion-arrow"
                              aria-hidden="true"
                            >
                              ↗
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                {/* OCCUPATION MATCH CONFIRMATION */}

                {hasOccupationMatch && (
                  <div
                    className="occupation-match"
                    role="status"
                  >
                    <span className="match-icon">✓</span>

                    <div>
                      <strong>Occupation selected</strong>

                      <p>
                        {occupation} has been selected for your assessment.
                      </p>
                    </div>
                  </div>
                )}

                {/* UNSUPPORTED OCCUPATION STATE */}

                {searchTerm &&
                  !hasOccupationMatch &&
                  filteredOccupations.length === 0 && (
                    <div
                      className="occupation-unavailable"
                      role="status"
                    >
                      <span className="information-icon">i</span>

                      <div>
                        <h3>Occupation not found</h3>

                        <p>
                          We couldn't find a match for the occupation
                          you entered. Please try an alternative or
                          related job title.
                        </p>

                        <p>
                          If no suitable match is available, an
                          assessment cannot be generated for this
                          occupation at this time.
                        </p>
                      </div>
                    </div>
                  )}

                <div className="occupation-data-note">
                  <strong>About occupation coverage</strong>

                  <p>
                    Occupation availability will depend on the
                    confirmed dataset and model coverage. The
                    current list is illustrative and will be
                    replaced during backend integration.
                  </p>
                </div>
              </div>
            </>
          )}

          {/* ========================================
              STEP 4: REVIEW
              ======================================== */}

          {currentStep === 3 && (
            <>
              <div className="assessment-section-heading">
                <span className="section-number">04</span>

                <div>
                  <h2>Review your assessment</h2>

                  <p>
                    Confirm your responses before submitting
                    your assessment.
                  </p>
                </div>
              </div>

              <div className="review-grid">

                {/* BACKGROUND SUMMARY */}

                <div className="review-card">
                  <div className="review-card-header">
                    <span className="review-label">
                      BACKGROUND
                    </span>

                    <button
                      type="button"
                      className="edit-response"
                      onClick={() => editStep(0)}
                    >
                      Edit responses
                    </button>
                  </div>

                  {hasBackgroundInformation ? (
                    <div className="review-background">
                      {educationLabel && (
                        <div className="review-detail">
                          <span>Education</span>
                          <strong>{educationLabel}</strong>
                        </div>
                      )}

                      {careerStageLabel && (
                        <div className="review-detail">
                          <span>Career stage</span>
                          <strong>{careerStageLabel}</strong>
                        </div>
                      )}

                      {experience && (
                        <div className="review-detail">
                          <span>Work experience</span>

                          <strong>
                            {experience === 'Less than 1'
                              ? 'Less than 1 year'
                              : experience}
                          </strong>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="optional-review-note">
                      Optional background information was skipped.
                    </p>
                  )}
                </div>

                {/* OCCUPATION SUMMARY */}

                <div className="review-card">
                  <div className="review-card-header">
                    <span className="review-label">
                      OCCUPATION
                    </span>

                    <button
                      type="button"
                      className="edit-response"
                      onClick={() => editStep(2)}
                    >
                      Edit responses
                    </button>
                  </div>

                  <h3>{occupation}</h3>

                  <div className="review-occupation-status">
                    <span>✓</span>
                    Occupation selected
                  </div>
                </div>

                {/* WORK VALUES SUMMARY */}

                <div className="review-card review-values-card">
                  <div className="review-card-header">
                    <span className="review-label">
                      YOUR WORK VALUES
                    </span>

                    <button
                      type="button"
                      className="edit-response"
                      onClick={() => editStep(1)}
                    >
                      Edit responses
                    </button>
                  </div>

                  <div className="review-values-grid">
                    {workValueOptions
                      .filter(
                        (value) =>
                          workValues[value.key] !== undefined
                      )
                      .map((value) => (
                        <div
                          className="review-value-item"
                          key={value.key}
                        >
                          <span>{value.label}</span>

                          <div className="review-rating">
                            <div
                              className="review-rating-bars"
                              aria-hidden="true"
                            >
                              {[1, 2, 3, 4, 5].map((rating) => (
                                <span
                                  key={rating}
                                  className={
                                    rating <= workValues[value.key]
                                      ? 'filled'
                                      : ''
                                  }
                                />
                              ))}
                            </div>

                            <strong>
                              {workValues[value.key]}/5
                            </strong>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              </div>

              {/* TEMPORARY SUBMISSION CONFIRMATION */}

              {submitted && (
                <div
                  className="submission-confirmation"
                  role="status"
                >
                  <span className="confirmation-icon">✓</span>

                  <div>
                    <h3>Assessment complete</h3>

                    <p>
                      Your responses are ready for the prototype
                      demonstration. Prediction results will become
                      available after model integration.
                    </p>
                  </div>
                </div>
              )}
            </>
          )}

          {/* VALIDATION MESSAGE */}

          {validationMessage && (
            <div
              className="assessment-validation"
              role="alert"
            >
              {validationMessage}
            </div>
          )}
        </div>

        {/* ========================================
            ASSESSMENT NAVIGATION
            ======================================== */}

        <div className="assessment-actions">
          <p>
            Provisional fields only. Responses are not yet
            connected to the prediction model.
          </p>

          <div className="assessment-buttons">
            {currentStep > 0 && (
              <button
                type="button"
                className="assessment-back"
                onClick={previousStep}
              >
                Back
              </button>
            )}

            {currentStep < steps.length - 1 && (
              <button
                type="button"
                className="assessment-next"
                onClick={nextStep}
              >
                Continue →
              </button>
            )}

            {currentStep === steps.length - 1 && (
              <button
                type="button"
                className="assessment-next"
                onClick={submitAssessment}
                disabled={submitted}
              >
                {submitted
                  ? 'Assessment Complete ✓'
                  : 'Submit Assessment →'}
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}