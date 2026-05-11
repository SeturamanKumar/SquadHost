import { installationContent } from "@/lib/docsContent";
import styles from "./Section.module.css";

function hasWarning(step: any): step is { warning: string } {
  return 'warning' in step && typeof step.warning === 'string';
}

export default function Installation() {
  const { heading, intro, prerequisites, steps, linuxDeployment, windowsDeployment, verification, teardown, nextSteps } = installationContent;

  return (
    <section id="installation" className={styles.section}>
      <h2 className={styles.heading}>{heading}</h2>

      <p className={styles.paragraph}>{intro.text}</p>

      {/* Prerequisites */}
      <h3 className={styles.subheading}>{prerequisites.subheading}</h3>
      <ul className={styles.list}>
        {prerequisites.items.map((item, i) => (
          <li key={i} className={styles.listItem}>{item}</li>
        ))}
      </ul>
      <p className={styles.note}>{prerequisites.note}</p>

      {/* Common Steps */}
      {steps.map((step, i) => (
        <div key={i} className={styles.step}>
          <h4 className={styles.stepTitle}>{step.title}</h4>
          {step.command && <CodeBlock command={step.command} />}
          {step.note && <p className={styles.note}>{step.note}</p>}
          {hasWarning(step) && step.warning && <p className={styles.warning}>{step.warning}</p>}
        </div>
      ))}

      {/* Linux Deployment */}
      <h3 className={styles.subheading}>{linuxDeployment.subheading}</h3>
      {linuxDeployment.steps.map((step, i) => (
        <div key={i} className={styles.step}>
          <h4 className={styles.stepTitle}>{step.title}</h4>
          {step.command && <CodeBlock command={step.command} />}
          {step.note && <p className={styles.note}>{step.note}</p>}
          {hasWarning(step) && step.warning && <p className={styles.warning}>{step.warning}</p>}
        </div>
      ))}

      {/* Windows Deployment */}
      <h3 className={styles.subheading}>{windowsDeployment.subheading}</h3>
      {windowsDeployment.steps.map((step, i) => (
        <div key={i} className={styles.step}>
          <h4 className={styles.stepTitle}>{step.title}</h4>
          {step.command && <CodeBlock command={step.command} />}
          {step.note && <p className={styles.note}>{step.note}</p>}
          {hasWarning(step) && step.warning && <p className={styles.warning}>{step.warning}</p>}
        </div>
      ))}

      {/* Verification */}
      <h3 className={styles.subheading}>{verification.subheading}</h3>
      {verification.text.map((p, i) => (
        <p key={i} className={styles.paragraph}>{p}</p>
      ))}

      {/* Teardown */}
      <h3 className={styles.subheading}>{teardown.subheading}</h3>
      <p className={styles.paragraph}>{teardown.text}</p>
      {teardown.command && <CodeBlock command={teardown.command} />}
      {teardown.warning && <p className={styles.warning}>{teardown.warning}</p>}

      {/* Next Steps */}
      <h3 className={styles.subheading}>{nextSteps.subheading}</h3>
      <p className={styles.paragraph}>{nextSteps.text}</p>
    </section>
  );
}

function CodeBlock({ command }: { command: string }) {
  return (
    <pre className={styles.codeBlock}>
      <code>{command}</code>
    </pre>
  );
}
