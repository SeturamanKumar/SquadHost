// ── Why SquadHost? ──
export const whySquadHostContent = {
  heading: "Why SquadHost?",
  problem: {
    subheading: "The Problem",
    text: [
      "Traditional Minecraft hosting charges you a flat monthly fee — $5 to $30 per month — even when your server sits idle 90% of the time. You pay for RAM and CPU that nobody is using.",
      "Free hosting services like Aternos make you wait in queues and limit your control. You can't install custom mods, and the server shuts down when you're not looking.",
      "Self-hosting on a VPS gives you control, but you still pay for the machine 24/7. And if your friends stop playing for a week, the bill doesn't stop.",
    ],
  },
  solution: {
    subheading: "What SquadHost Does",
    bulletPoints: [
      "Launches a Minecraft server on your own AWS account only when you click 'Launch'.",
      "Automatically terminates the server after 8 minutes of zero players — the Kamikaze protocol.",
      "Master node terminates itself when no game servers are active for 10 minutes — true scale-to-zero billing.",
      "World data is saved to S3 and restored on next launch — infinite persistence without infinite cost.",
      "No monthly subscription. You pay AWS directly for only the compute seconds you actually use.",
      "Full control: you own the AWS account, the files, and the configuration.",
    ],
  },
  pricingExample: {
    subheading: "How Cheap Is It?",
    text: [
      "A typical 2-hour play session with friends on a t3.medium instance costs roughly $0.06–0.12 total. If nobody plays for a week, your AWS bill for that week is $0.00.",
      "AWS gives new accounts $100 in free credits. That covers months of casual gameplay.",
      "Compare that to a $10/month hosting plan that sits idle. SquadHost puts the savings in your pocket.",
    ],
  },
};

// ── What is SquadHost? ──
export const whatIsSquadHostContent = {
  heading: "What is SquadHost?",
  overview: {
    subheading: "At a Glance",
    text: [
      "SquadHost is an open-source, self-deployed Minecraft server platform that runs on your own Amazon Web Services (AWS) account. Think of it as your personal Aternos clone — but with no queues, full mod support (coming soon), and complete control over your infrastructure.",
    ],
  },
  architecture: {
    subheading: "How It Works",
    bulletPoints: [
      "Web Dashboard (Next.js) — A clean single-page dashboard to launch, monitor, and manage your Minecraft servers.",
      "Backend API (Django) — Handles server creation, status tracking, and orchestrates the cloud lifecycle.",
      "Master Node (EC2) — A lightweight supervisor running both the frontend and backend via Docker Compose.",
      "Game Servers (EC2) — Minecraft servers each running in an isolated Docker container, provisioned on demand.",
      "World Storage (S3) — All world data, configs, and (soon) mods are stored durably and synced on launch/shutdown.",
      "Lambda Functions — Handle server creation and status updates, triggered by the Django backend.",
      "Kamikaze Watchdog — Python scripts that monitor player count and terminate idle servers automatically.",
    ],
  },
  techStack: {
    subheading: "Technology Stack",
    items: [
      "Infrastructure as Code: Terraform",
      "Configuration Management: Ansible",
      "Container Runtime: Docker & Docker Compose",
      "Cloud Provider: AWS (EC2, S3, Lambda, IAM, VPC, RDS)",
      "Frontend: Next.js (React, TypeScript)",
      "Backend: Django (Python) + Django REST Framework",
      "Database: PostgreSQL (via RDS)",
      "CI/CD: GitHub Actions",
    ],
  },
  comparison: {
    subheading: "SquadHost vs. Traditional Hosting",
    rows: [
      { feature: "Monthly Cost", traditional: "$5–$30/month fixed", squadhost: "~$0.50–$3/month for typical usage" },
      { feature: "Idle Cost", traditional: "Full price, even when empty", squadhost: "$0.00 — servers are terminated" },
      { feature: "Queue Times", traditional: "Free hosts make you wait", squadhost: "No queues — your own AWS account" },
      { feature: "Mod Support", traditional: "Often limited or requires upgrade", squadhost: "Coming soon — planned after core stability" },
      { feature: "Server Control", traditional: "Shared panel, limited access", squadhost: "Full root access, your own AWS account" },
      { feature: "Setup Complexity", traditional: "Sign up, pay, play", squadhost: "One-time 10-15 minute Docker deployment" },
      { feature: "Data Ownership", traditional: "On provider's machines", squadhost: "Your AWS account, your data, your rules" },
    ],
  },
};

interface InstallationStep {
  title: string;
  command: string;
  note?: string;
  warning?: string;
}

// ── Installation ──
export const installationContent = {
  heading: "Installation",
  intro: {
    text: "SquadHost is fully containerized. You do not need to install Terraform, Ansible, or the AWS CLI on your machine. The only requirement is Docker and an AWS account. The entire deployment takes 10–15 minutes.",
  },
  prerequisites: {
    subheading: "Prerequisites",
    items: [
      "Docker installed and running on your machine.",
      "An AWS account with a valid credit/debit card for identity verification.",
      "~10–15 minutes for the initial deployment to complete.",
    ],
    note: "You do NOT need to install Terraform, Ansible, or the AWS CLI natively — everything runs inside Docker.",
  },
  steps: [
  {
    title: "Step 1: Clone the Repository",
    command: "git clone https://github.com/SeturamanKumar/SquadHost.git\ncd SquadHost",
    note: "This pulls the entire project: frontend, backend, infrastructure code, and deployment scripts.",
    warning: ""
  },
  {
    title: "Step 2: Configure the .env File",
    command: "# From the project root, duplicate the template file:\ncp aws_credentials.env.template aws_credentials.env\n\n# Open aws_credentials.env in your text editor",
    note: "This is where your AWS credentials will go. Also change the default TF_VAR_db_username and TF_VAR_db_password values to secure credentials of your choice before deploying. This file is git-ignored — your secrets are safe.",
    warning: ""
  },
  {
    title: "Step 3: Create an AWS Account",
    command: "# Follow the official AWS guide to create your account:\n# https://repost.aws/knowledge-center/create-and-activate-aws-account",
    warning: "AWS requires a valid credit card for identity verification. New accounts receive $100 in credits and Free Tier benefits (750 hours of small EC2 instances/month for the first year). Once your credits or Free Tier limits are exhausted, AWS will charge your card. SquadHost's Kamikaze architecture minimizes costs, but you are responsible for any charges. Expected cost: roughly $0.06 per hour of gameplay, well within the free credits.",
    note: "During signup, make sure to select the Basic support - Free plan."
  },
  {
    title: "Step 4: Generate AWS Credentials",
    command: "# Follow the official AWS guide to create an IAM Access Key:\n# https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html",
    warning: "AWS only shows the Secret Access Key once! Copy it immediately. Create keys for a user with programmatic access.",
    note: "Once generated, paste the three values into your aws_credentials.env file:\n• AWS_ACCESS_KEY_ID — Your public account identifier\n• AWS_SECRET_ACCESS_KEY — Your private password\n• AWS_DEFAULT_REGION — The region closest to you (e.g., ap-south-1, us-east-1)"
  },
  {
    title: "Step 5: Deploy (OS-Specific)",
    command: "",
    note: "Choose your operating system below and follow the specific instructions.",
    warning: ""
  }
] as InstallationStep[],
  linuxDeployment: {
    subheading: "Linux Deployment",
    steps: [
      {
        title: "Install Docker",
        command:
          "curl -fsSL https://get.docker.com -o get-docker.sh\nsudo sh get-docker.sh\nsudo usermod -aG docker $USER\nnewgrp docker",
        note: "The convenience script installs Docker Engine for your distribution. Adding your user to the docker group avoids needing sudo for every command.",
      },
      {
        title: "Make Scripts Executable",
        command: "chmod +x docker_spin_up.sh docker_kill_all.sh",
      },
      {
        title: "Ignite the Cloud",
        command: "./docker_spin_up.sh",
        note: "This single command does everything: builds Docker images, initializes Terraform, provisions your AWS infrastructure, configures the EC2 instances with Ansible, and launches the dashboard. Wait 10–15 minutes for completion.",
      },
    ],
  },
  windowsDeployment: {
    subheading: "Windows Deployment",
    steps: [
      {
        title: "Enable WSL 2",
        command: '# In PowerShell (Run as Administrator):\nwsl --install',
        note: "Docker Desktop requires WSL 2. You may need to restart your computer after this step if WSL was not previously installed.",
      },
      {
        title: "Install Docker Desktop",
        command:
          "# Search 'Docker Desktop' in the Microsoft Store and install.\n# Open Docker Desktop from the Start Menu.\n# Wait for the whale icon in the system tray to stop animating.",
        note: "You may need to create a Docker account (you can use your Gmail).",
      },
      {
        title: "Verify Docker",
        command: "# In PowerShell:\ndocker ps",
        note: "If it returns a list (even empty), Docker is ready. If there's an error, wait 30 seconds and try again.",
      },
      {
        title: "Ignite the Cloud",
        command: "# Right-click docker_spin_up.bat and select Run as administrator",
        warning:
          "The terminal window must stay open for the entire 10–15 minute deployment. Do NOT close it or press Ctrl+C.",
      },
    ],
  },
  verification: {
    subheading: "Verify Everything Works",
    text: [
      "After the deployment script completes, it will output the public IP address of your master node.",
      "Open your browser and navigate to http://<master-node-ip> — you should see the SquadHost dashboard.",
      "From the dashboard, click 'Create Server', choose your specs, and launch.",
      "Wait 5–6 minutes for the EC2 instance to provision and the Minecraft server to start.",
      "Connect to the server IP shown in the dashboard from your Minecraft client.",
    ],
  },
  teardown: {
    subheading: "Stopping Everything (Nuclear Teardown)",
    text: "When you're done playing and want to stop all AWS billing:",
    command: "./docker_kill_all.sh   # Linux\n# or\ndocker_kill_all.bat       # Windows",
    warning:
      "This permanently destroys all AWS resources including game servers. Any worlds not manually backed up from S3 will be lost. You can always run docker_spin_up.sh again to redeploy from scratch.",
  },
  nextSteps: {
    subheading: "Next Steps",
    text: "Read the Usage section to learn about creating and managing servers, monitoring costs, and the Kamikaze protocol. Mod support is planned for a future release.",
  },
};

// ── Usage ──
export const usageContent = {
  heading: "Usage",
  creatingServer: {
    subheading: "Creating a Server",
    text: "From the dashboard, click 'Create Server' and configure your Minecraft server:",
    options: [
      "Server name — A friendly name to identify your server.",
      "Minecraft version — Choose from available versions (Vanilla, Paper, etc.).",
      "Server RAM — How much memory to allocate (1–16 GB).",
      "World seed (optional) — Generate a specific world.",
      "Ops players — Usernames of players who will have admin privileges.",
    ],
    note: "After creation, the server will be in 'Pending' state. Wait 5–6 minutes while AWS provisions the EC2 instance and the Minecraft server starts. Once ready, the dashboard shows the server IP.",
  },
  playing: {
    subheading: "Connecting to Your Server",
    text: [
      "Copy the server IP from the dashboard.",
      "Open Minecraft and go to Multiplayer → Direct Connect.",
      "Paste the IP and join. You're playing on your own AWS server!",
    ],
  },
  modding: {
    subheading: "Mod Support (Coming Soon)",
    text: "Mod support is a planned feature currently in development. Once released, you will be able to upload mod .jar files through the dashboard or specify a modpack URL, and they will be automatically deployed to your server. In the meantime, you can manually SSH into your game server instance and add mods directly — just remember they will be lost when the server terminates unless you also upload them to S3.",
    note: "Mod support is the next major feature planned after the current cybersecurity hardening phase. Follow the project on GitHub for updates.",
  },
  serverManagement: {
    subheading: "Managing Servers",
    items: [
      "Launch — Start a new server or wake an existing one.",
      "Stop — Gracefully shut down the server (saves world to S3).",
      "Status — See real-time status: Pending, Starting, Running, Stopping, Error.",
      "Console Output — View live logs from the Minecraft server directly in the dashboard.",
    ],
  },
  costMonitoring: {
    subheading: "Understanding Costs",
    text: "Since SquadHost runs on your AWS account, all costs are visible in the AWS Billing Console. The Kamikaze protocol aggressively terminates idle servers, so you only pay for active gameplay time. You can set up budget alerts in the AWS Console to notify you if costs exceed a threshold.",
    tip: "Check your AWS Free Tier usage in the Billing Console. For most casual players, the $100 in credits covers months of play. A typical 2-hour session with 4 players costs roughly $0.06–0.12.",
  },
};

// ── Monitoring & Alerts ──
export const monitoringAlertsContent = {
  heading: "Monitoring & Alerts",
  kamikazeProtocol: {
    subheading: "The Kamikaze Protocol",
    text: [
      "Every game server runs a watchdog script (kamikaze_watchdog.py) that monitors player count via RCON. If the server has zero players for 8 minutes, the watchdog triggers a graceful shutdown: the world is zipped, uploaded to S3, and the EC2 instance terminates itself — immediately halting all billing for that server.",
      "The Master Node runs a similar watchdog. If no game servers are active for 10 minutes, it backs up the PostgreSQL database to S3, saves all world data, and terminates itself. This is the true scale-to-zero moment — your AWS bill drops to $0.00 until the next deployment.",
    ],
  },
  dashboardIndicators: {
    subheading: "Dashboard Status Indicators",
    items: [
      "Pending — The server is queued for provisioning.",
      "Starting — EC2 instance is booting and Minecraft is starting up.",
      "Running — Server is live and accepting connections.",
      "Stopping — The Kamikaze protocol has triggered; world is being saved.",
      "Error — Something went wrong; check console output for details.",
    ],
  },
  futurePlans: {
    subheading: "Planned: Prometheus Monitoring",
    text: "A future update will integrate Prometheus and Grafana for detailed monitoring: player counts, TPS (ticks per second), memory usage, and cost estimates. This will be exposed via a metrics endpoint on each server and on the master node. Check the GitHub repository for roadmap updates.",
  },
};

// ── Troubleshooting ──
export const troubleshootingContent = {
  heading: "Troubleshooting",
  commonIssues: [
    {
      issue: "Deployment fails immediately with an auth error",
      cause: "Your AWS credentials are incorrect or have trailing spaces.",
      solutions: [
        "Double-check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in aws_credentials.env.",
        "Make sure there are no trailing spaces at the end of each line.",
        "Ensure the IAM user has programmatic access enabled and sufficient permissions (EC2, RDS, S3, Lambda, IAM).",
      ],
    },
    {
      issue: "Resources created in the wrong AWS region",
      cause: "AWS_DEFAULT_REGION in aws_credentials.env is incorrect.",
      solutions: [
        "Verify AWS_DEFAULT_REGION matches the region shown in the top-right corner of your AWS console.",
        "Redeploy with the correct region. You may need to destroy existing resources first.",
      ],
    },
    {
      issue: "Terraform state corruption after interrupted deployment",
      cause: "You pressed Ctrl+C during deployment, leaving partial resources.",
      solutions: [
        "Never press Ctrl+C during docker_spin_up. If it happens: manually delete any partially created resources in the AWS console, then delete the squadhost-tfstate-<account-id> S3 bucket before re-running.",
        "Run docker_kill_all to clean up, then redeploy.",
      ],
    },
    {
      issue: 'Server shows "Pending" or "Pending AWS IP..." for too long',
      cause: "EC2 instance provisioning and Minecraft startup takes time.",
      solutions: [
        "Wait 5–6 minutes. EC2 provisioning, Docker image pulls, and Minecraft startup all take time.",
        "If it persists beyond 10 minutes, check the console output in the dashboard for error messages.",
      ],
    },
    {
      issue: "Docker not found or permission denied",
      cause: "Docker daemon is not running, or your user lacks permissions.",
      solutions: [
        "On Linux: run sudo systemctl start docker to start the daemon.",
        "Ensure you added your user to the docker group (sudo usermod -aG docker $USER) and ran newgrp docker.",
        "On Windows: wait for the Docker Desktop whale icon to stop animating before running the script.",
      ],
    },
    {
      issue: "Can't connect to the Minecraft server from my client",
      cause: "The server might still be starting, or a security group is blocking the port.",
      solutions: [
        "Wait a full 5–6 minutes after launching. The dashboard status should show 'Running'.",
        "Ensure your security group allows inbound TCP on port 25565 from 0.0.0.0/0.",
        "Verify you're using the correct IP shown in the dashboard.",
      ],
    },
  ],
  gettingHelp: {
    subheading: "Getting More Help",
    text: "If you can't resolve an issue using the steps above, please open a GitHub Issue in the SquadHost repository. Include your console output (from the dashboard), the steps you've already tried, and the approximate time the problem occurred.",
    links: [
      { label: "GitHub Issues", url: "https://github.com/SeturamanKumar/SquadHost/issues" },
      { label: "Email Support", url: "mailto:kumar.seturaman@gmail.com" },
    ],
  },
};

// ── Contributions ──
export const contributionsContent = {
  heading: "Contributions",
  welcome: {
    subheading: "Welcome",
    text: "SquadHost is an open-source project, and contributions of all kinds are welcome — from bug reports and documentation improvements to new features and infrastructure enhancements.",
  },
  waysToContribute: {
    subheading: "Ways to Contribute",
    items: [
      "Report a bug — Open an issue with clear steps to reproduce.",
      "Improve documentation — Fix typos, add missing steps, or translate content.",
      "Submit code — Pick an open issue and send a pull request.",
      "Share ideas — Start a discussion about new features or better architecture.",
      "Test and give feedback — Spin up SquadHost, play with friends, and tell us what could be better.",
    ],
  },
  developmentSetup: {
    subheading: "Development Setup",
    text: "To start contributing code, you'll need a working local development environment.",
    steps: [
      {
        title: "1. Fork & Clone",
        command: "git clone https://github.com/YOUR_USERNAME/SquadHost.git\ncd SquadHost",
      },
      {
        title: "2. Install Dependencies",
        command:
          "# Frontend\ncd client && npm install\n\n# Backend\ncd ../server && pip install -r requirements.txt",
      },
      {
        title: "3. Run Locally",
        command:
          "# Terminal 1: Backend\ncd server && python manage.py runserver\n\n# Terminal 2: Frontend\ncd client && npm run dev",
        note: "You can now access the dashboard at http://localhost:3000. Local development uses SQLite by default.",
      },
      {
        title: "4. Make Your Changes",
        command: "git checkout -b my-feature\n# Make your changes, test locally, then commit.",
      },
      {
        title: "5. Submit a Pull Request",
        command: "git push origin my-feature\n# Open a PR on GitHub from your branch.",
        note: "Please follow the existing code style and include a clear description of what you changed and why.",
      },
    ],
  },
  codeOfConduct: {
    subheading: "Code of Conduct",
    text: "All contributors are expected to be respectful and constructive. Harassment, spam, or disruptive behavior will not be tolerated. We're here to build something great together.",
  },
};
