import { monitoringAlertsContent } from "@/lib/docsContent";
import styles from "./Section.module.css";

export default function MonitoringAlerts() {
  const { heading, kamikazeProtocol, dashboardIndicators, futurePlans } = monitoringAlertsContent;

  return (
    <section id="monitoring-alerts" className={styles.section}>
      <h2 className={styles.heading}>{heading}</h2>

      <h3 className={styles.subheading}>{kamikazeProtocol.subheading}</h3>
      {kamikazeProtocol.text.map((p, i) => (
        <p key={i} className={styles.paragraph}>{p}</p>
      ))}

      <h3 className={styles.subheading}>{dashboardIndicators.subheading}</h3>
      <ul className={styles.list}>
        {dashboardIndicators.items.map((item, i) => (
          <li key={i} className={styles.listItem}>{item}</li>
        ))}
      </ul>

      <h3 className={styles.subheading}>{futurePlans.subheading}</h3>
      <p className={styles.paragraph}>{futurePlans.text}</p>
    </section>
  );
}
