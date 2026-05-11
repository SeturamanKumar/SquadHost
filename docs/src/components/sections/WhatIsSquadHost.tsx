import { whatIsSquadHostContent } from "@/lib/docsContent";
import styles from "./Section.module.css";

export default function WhatIsSquadHost() {
  const { heading, overview, architecture, techStack, comparison } = whatIsSquadHostContent;

  return (
    <section id="what-is-squadhost" className={styles.section}>
      <h2 className={styles.heading}>{heading}</h2>

      <h3 className={styles.subheading}>{overview.subheading}</h3>
      {overview.text.map((p, i) => (
        <p key={i} className={styles.paragraph}>{p}</p>
      ))}

      <h3 className={styles.subheading}>{architecture.subheading}</h3>
      <ul className={styles.list}>
        {architecture.bulletPoints.map((item, i) => (
          <li key={i} className={styles.listItem}>{item}</li>
        ))}
      </ul>

      <h3 className={styles.subheading}>{techStack.subheading}</h3>
      <div className={styles.tagCloud}>
        {techStack.items.map((item, i) => (
          <span key={i} className={styles.tag}>{item}</span>
        ))}
      </div>

      <h3 className={styles.subheading}>{comparison.subheading}</h3>
      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Feature</th>
              <th>Traditional Host</th>
              <th>SquadHost</th>
            </tr>
          </thead>
          <tbody>
            {comparison.rows.map((row, i) => (
              <tr key={i}>
                <td>{row.feature}</td>
                <td>{row.traditional}</td>
                <td>{row.squadhost}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
