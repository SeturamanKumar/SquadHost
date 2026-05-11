import { usageContent } from "@/lib/docsContent";
import styles from "./Section.module.css";

export default function Usage() {
  const { heading, creatingServer, playing, modding, serverManagement, costMonitoring } = usageContent;

  return (
    <section id="usage" className={styles.section}>
      <h2 className={styles.heading}>{heading}</h2>

      <h3 className={styles.subheading}>{creatingServer.subheading}</h3>
      <p className={styles.paragraph}>{creatingServer.text}</p>
      <ul className={styles.list}>
        {creatingServer.options.map((opt, i) => (
          <li key={i} className={styles.listItem}>{opt}</li>
        ))}
      </ul>
      <p className={styles.note}>{creatingServer.note}</p>

      <h3 className={styles.subheading}>{playing.subheading}</h3>
      {playing.text.map((p, i) => (
        <p key={i} className={styles.paragraph}>{p}</p>
      ))}

      <h3 className={styles.subheading}>{modding.subheading}</h3>
      <p className={styles.paragraph}>{modding.text}</p>
      <p className={styles.note}>{modding.note}</p>

      <h3 className={styles.subheading}>{serverManagement.subheading}</h3>
      <ul className={styles.list}>
        {serverManagement.items.map((item, i) => (
          <li key={i} className={styles.listItem}>{item}</li>
        ))}
      </ul>

      <h3 className={styles.subheading}>{costMonitoring.subheading}</h3>
      <p className={styles.paragraph}>{costMonitoring.text}</p>
      <p className={styles.note}>{costMonitoring.tip}</p>
    </section>
  );
}
