import './About.css';

const dimensions = [
  {
    title: 'Skills',
    description: 'What a person can do.',
    number: '01',
  },
  {
    title: 'Work Values',
    description: 'What matters to a person at work.',
    number: '02',
  },
  {
    title: 'Interests',
    description: 'What a person enjoys and wants to pursue.',
    number: '03',
  },
  {
    title: 'Work Activities',
    description: 'The nature of the work a person performs.',
    number: '04',
  },
];

export default function About() {
  return (
    <section className="about-page">
      <header className="about-header">
        <span className="about-eyebrow">
          ABOUT THE PROJECT
        </span>

        <h1>Connecting People to Meaningful Work</h1>

        <p>
          Exploring how personal work values and occupational
          alignment relate to job satisfaction.
        </p>
      </header>

      <div className="about-card">
        <div className="about-card-heading">
          <span className="about-section-number">01</span>
          <h2>About swytch</h2>
        </div>

        <p>
          Founded in Boulder, Colorado, in 2024, swytch helps
          organizations identify talent beyond traditional
          resumes and job titles by considering four
          dimensions of alignment.
        </p>

        <div className="about-dimensions">
          {dimensions.map((dimension) => (
            <div
              className="about-dimension"
              key={dimension.title}
            >
              <span className="about-dimension-number">
                {dimension.number}
              </span>

              <div>
                <h3>{dimension.title}</h3>
                <p>{dimension.description}</p>
              </div>
            </div>
          ))}
        </div>

        <p>
          Its approach combines technology with human
          judgment to support more informed and sustainable
          career matches, with an initial focus on aerospace
          and advanced manufacturing.
        </p>

        <a
          className="about-link"
          href="https://swytch.careers/"
          target="_blank"
          rel="noopener noreferrer"
        >
          Visit swytch.careers ↗
        </a>
      </div>

      <div className="about-card">
        <div className="about-card-heading">
          <span className="about-section-number">02</span>
          <h2>Our Project</h2>
        </div>

        <p>
          Developed through the Break Through Tech AI Studio
          program, this project aims to predict job
          satisfaction based on how closely an individual's
          personal work values align with what their job
          offers.
        </p>

        <div className="about-research-question">
          <span>OUR RESEARCH QUESTION</span>

          <h3>
            Can aligning people with what they value at work,
            rather than relying on job titles alone, help
            predict job satisfaction?
          </h3>
        </div>

        <p>
          This research tests a core idea behind swytch:
          that matching people based on what matters to them
          can contribute to better employment outcomes.
        </p>
      </div>

      <div className="about-card">
        <div className="about-card-heading">
          <span className="about-section-number">03</span>
          <h2>Data &amp; Research</h2>
        </div>

        <p>
          Our research draws on occupational and
          individual-level data to explore the relationship
          between work-value alignment and job satisfaction.
        </p>

        <div className="about-datasets">
          <div className="about-dataset">
            <span className="about-dataset-label">
              OCCUPATIONAL DATA
            </span>

            <h3>O*NET</h3>

            <h4>Occupational Information Network</h4>

            <p>
              Provides information about occupational
              characteristics, work values and work activities.
            </p>

            <a
              className="about-link"
              href="https://www.onetonline.org/"
              target="_blank"
              rel="noopener noreferrer"
            >
              Explore O*NET ↗
            </a>
          </div>

          <div className="about-dataset about-dataset-pending">
            <span className="about-dataset-label">
              ADDITIONAL DATA
            </span>

            <h3>Additional dataset</h3>

            <p>
              Pending confirmation from the research team.
            </p>
          </div>
        </div>
      </div>

      <div className="about-card">
        <div className="about-card-heading">
          <span className="about-section-number">04</span>
          <h2>Responsible Use</h2>
        </div>

        <p>
          This application is a research prototype designed
          to support career exploration and informed
          decision-making.
        </p>

        <div className="about-responsible-notice">
          <strong>Supporting, not replacing, human judgment</strong>

          <p>
            Predictions should not be interpreted as
            guarantees of job satisfaction or definitive
            measures of career suitability. The application
            is not a substitute for professional judgment.
          </p>
        </div>
      </div>

      <footer className="about-footer">
        Developed by Team Swytch 2C
        <span className="about-footer-dot"> · </span>
        Break Through Tech AI
        <span className="about-footer-dot"> · </span>
        Fall 2026
      </footer>
    </section>
  );
}