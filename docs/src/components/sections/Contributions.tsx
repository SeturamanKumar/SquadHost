import { contributionsContent } from "@/lib/docsContent";
import styles from "./Section.module.css";

export default function Contributions() {
  const { heading, welcome, waysToContribute, developmentSetup, codeOfConduct } = contributionsContent;

  return (
    <section id="contributions" className={styles.section}>
      <h2 className={styles.heading}>{heading}</h2>

      <h3 className={styles.subheading}>{welcome.subheading}</h3>
      <p className={styles.paragraph}>{welcome.text}</p>

      <h3 className={styles.subheading}>{waysToContribute.subheading}</h3>
      <ul className={styles.list}>
        {waysToContribute.items.map((item, i) => (
          <li key={i} className={styles.listItem}>{item}</li>
        ))}
      </ul>

      <h3 className={styles.subheading}>{developmentSetup.subheading}</h3>
      <p className={styles.paragraph}>{developmentSetup.text}</p>
      {developmentSetup.steps.map((step, i) => (
        <div key={i} className={styles.step}>
          <h4 className={styles.stepTitle}>{step.title}</h4>
          {step.command && <pre className={styles.codeBlock}><code>{step.command}</code></pre>}
          {step.note && <p className={styles.note}>{step.note}</p>}
        </div>
      ))}

      <h3 className={styles.subheading}>{codeOfConduct.subheading}</h3>
      <p className={styles.paragraph}>{codeOfConduct.text}</p>
    </section>
  );
}
