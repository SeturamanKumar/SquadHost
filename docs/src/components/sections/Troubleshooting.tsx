import { troubleshootingContent } from "@/lib/docsContent";
import styles from "./Section.module.css";

export default function Troubleshooting() {
  const { heading, commonIssues, gettingHelp } = troubleshootingContent;

  return (
    <section id="troubleshooting" className={styles.section}>
      <h2 className={styles.heading}>{heading}</h2>

      {commonIssues.map((entry, i) => (
        <div key={i} className={styles.step}>
          <h3 className={styles.subheading}>{entry.issue}</h3>
          <p className={styles.paragraph}><strong>Cause:</strong> {entry.cause}</p>
          <p className={styles.paragraph}><strong>Solutions:</strong></p>
          <ul className={styles.list}>
            {entry.solutions.map((s, j) => (
              <li key={j} className={styles.listItem}>{s}</li>
            ))}
          </ul>
        </div>
      ))}

      <h3 className={styles.subheading}>{gettingHelp.subheading}</h3>
      <p className={styles.paragraph}>{gettingHelp.text}</p>
      <div className={styles.links}>
        {gettingHelp.links.map((link, i) => (
          <a key={i} href={link.url} className={styles.externalLink} target="_blank" rel="noopener noreferrer">
            {link.label} ↗
          </a>
        ))}
      </div>
    </section>
  );
}
