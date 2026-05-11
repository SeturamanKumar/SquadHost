import WhySquadHost from "@/components/sections/WhySquadHost";
import WhatIsSquadHost from "@/components/sections/WhatIsSquadHost";
import Installation from "@/components/sections/Installation";
import Usage from "@/components/sections/Usage";
import MonitoringAlerts from "@/components/sections/MonitoringAlerts";
import Troubleshooting from "@/components/sections/Troubleshooting";
import Contributions from "@/components/sections/Contributions";

export default function Home() {
  return (
    <>
      <WhySquadHost />
      <WhatIsSquadHost />
      <Installation />
      <Usage />
      <MonitoringAlerts />
      <Troubleshooting />
      <Contributions />
    </>
  );
}
