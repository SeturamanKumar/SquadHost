import { whySquadHostContent } from "@/lib/docsContent";
import styles from "./Section.module.css";

export default function WhySquadHost() {
  const { heading, problem, solution, pricingExample } = whySquadHostContent;

  return (
    <section id="why-squadhost" className={styles.section}>
      <h2 className={styles.heading}>{heading}</h2>

      <h3 className={styles.subheading}>{problem.subheading}</h3>
      {problem.text.map((p, i) => (
        <p key={i} className={styles.paragraph}>{p}</p>
      ))}

      <h3 className={styles.subheading}>{solution.subheading}</h3>
      <ul className={styles.list}>
        {solution.bulletPoints.map((item, i) => (
          <li key={i} className={styles.listItem}>{item}</li>
        ))}
      </ul>

      <h3 className={styles.subheading}>{pricingExample.subheading}</h3>
      {pricingExample.text.map((p, i) => (
        <p key={i} className={styles.paragraph}>{p}</p>
      ))}
    </section>
  );
}
