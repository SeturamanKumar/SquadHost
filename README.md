# SquadHost 🎮☁️

<details open>
<summary><strong>💡 About the Project</strong></summary>

SquadHost is an open-source, self-hosted Aternos clone. I built this project to solve a specific problem: wanting complete control over a Minecraft server (soon modded) without paying 24/7 cloud hosting fees or waiting in free-tier queues. 

Beyond solving a hosting problem, this project served as a practical proving ground for my engineering skills. I utilized it to actively learn Next.js and modern frontend development from scratch, while simultaneously designing a robust Python/Django backend and a highly automated DevOps pipeline.

### 🛠️ The Tech Stack
* **Frontend:** Next.js, React, TypeScript, CSS (Built to learn Next.js and implement server-side proxying).
* **Backend:** Python, Django, PostgreSQL, Django REST Framework.
* **DevOps & IaC:** Terraform, Ansible, Docker.
* **Cloud Infrastructure:** Amazon Web Services (EC2, S3, RDS, Lambda, IAM, VPC).

</details>

<details>
<summary><strong>🚀 Installation & Deployment Guide</strong></summary>

SquadHost is fully containerized. You do **not** need to install Terraform, Ansible, or the AWS CLI natively on your machine. You only need Docker and an Amazon Web Services (AWS) Account.

### Step 1: Configure the `.env` File
First, we need to set up the configuration file where your AWS keys will eventually go.
1. Clone this repository to your local machine.
2. Locate the `aws_credentials.env.template` file in the root directory.
3. Duplicate the file and rename the copy exactly to `aws_credentials.env`.
4. Keep this file open. We will paste your Access Key, Secret Key, and Region into it in Step 3. *(Note: This file is securely git-ignored to protect your AWS account).*

### Step 2: Create an AWS Account
> ⚠️ **Important Billing Warning:** AWS requires a valid credit card for identity verification. New accounts typically receive AWS Free Tier benefits, which act like a credit limit (often covering the first 750 hours of small EC2 instances per month for the first year). 
> 
> **However, AWS is not entirely free.** Once your Free Tier limits are exhausted, or your trial period ends, AWS will charge your linked card. While SquadHost's kamikaze architecture is aggressively cost-optimized, you are still financially responsible for any cloud resources you consume.
>
> **The expected cost** per month can reach upto 20$ which will be covered by the 100$ provided to you by AWS.

* If you do not already have an AWS account, please follow the [Official AWS Account Creation Guide](https://repost.aws/knowledge-center/create-and-activate-aws-account).
* **Crucial Step:** Ensure you select the **Basic support - Free** plan during the final signup step.

### Step 3: Generate AWS Credentials
To allow SquadHost to automatically provision your cloud infrastructure via Terraform, you need an AWS IAM Access Key. 
* Follow the [Official AWS IAM Access Key Guide](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html) to generate your credentials. 
* *Note: Ensure you create the keys for a user with programmatic access, and do not close the AWS window until you have copied the secret key!*

Once generated, AWS will provide you with three critical pieces of information. Paste these directly into the `aws_credentials.env` file you created in Step 1:
* **AWS_ACCESS_KEY_ID**: Your public account identifier.
* **AWS_SECRET_ACCESS_KEY**: Your private password *(AWS only shows this once!)*.
* **AWS_DEFAULT_REGION**: The data center closest to you (e.g., `ap-south-1`, `us-east-1`). You can find this in the top right corner of your AWS console.

### Step 4: OS-Specific Deployment
Select your operating system below to install Docker and ignite the cloud infrastructure.

<details>
<summary>🐧 <strong>Linux Deployment</strong></summary>

1. **Install Docker:** Install the Docker Engine using your distribution's package manager (e.g., `sudo pacman -S docker` or `sudo apt install docker.io`).
2. **Docker Permissions:** On Linux, grant permission to the Docker socket to run containers:
3. **Script Permissions:** Ensure the deployment scripts are executable:
4. **Ignite the Cloud:** Run the spin_up script:

```bash
sudo chmod 666 /var/run/docker.sock
chmod +x docker_spin_up.sgh docker_kill_all.sh
./docker_spin_up.sh
```

5. **Nuclear Teardown:** When you are done with Minecraft you can run this to delete everything in AWS to stop any billing. *(Note: This command will also delete any saved multiplayer worls you might have had).*

```bash
./docker_kill_all.sh
```
</details>

<details>
<summary>🪟 <strong>Windows Deployment</strong></summary>

1. **Install Docker:** Download and install Docker Desktop for Windows. You will need to Restart your computer after you installed Docker.
2. **Ignite the Cloud:** Double-click the following script and run it as administrator:

```
docker_spin_up.bat
```
3. **Nuclear Teardown:** When you are done with Minecraft you can run this to delete everything in AWS to stop any billing. *(Note: This command will also delete any saved multiplayer worls you might have had).*
```
docker_kill_all.bat
```
</details>

<details>
<summary>🍏 <strong>Mac Deployment</strong></summary>

1. **Install Docker:** Download and install Docker Desktop for Mac. Ensure Docker is running in your menu bar.
2. **Script Permissions:** Ensure the deployment scripts are executable:
3. **Ignite the Cloud:** Run the spin_up script:

```
sudo chmod 666 /var/run/docker.sock
chmod +x docker_spin_up.sgh docker_kill_all.sh
./docker_spin_up.sh
```
4. **Nuclear Teardown:** When you are done with Minecraft you can run this to delete everything in AWS to stop any billing. *(Note: This command will also delete any saved multiplayer worls you might have had).*

</details>
</details>

<details>
<summary><strong>🧠 Architecture Logic & Cloud Flow</strong></summary>

SquadHost is not just a standard web application; it is a fully automated cloud orchestrator designed to solve the primary problem of cloud gaming: paying for idle servers. 

To achieve a true "scale-to-zero" environment, this project utilizes a custom cloud lifecycle pipeline.

### 1. The Kamikaze Approach (Cost Optimization)
The core feature of SquadHost is the "Kamikaze" auto-deletion protocol. Cloud providers bill by the second for running EC2 instances. To minimize this, the architecture is designed to self-destruct when no longer needed.
* **The Watchdog:** When a server is provisioned, Ansible injects a Bash watchdog script (`kamikaze.sh`) into the worker node.
* **Inactivity Monitoring:** This script continuously polls the Dockerized Minecraft container via RCON to check the active player count.
* **The 1-Hour Guillotine:** If the player count remains at exactly 0 for 1 continuous hour, the script triggers the shutdown sequence.
* **Self-Termination:** The script safely stops the container, zips the world files, pushes the backup to AWS S3, and finally uses the AWS Metadata API to invoke the `ec2:TerminateInstances` permission, physically deleting its own host server from your AWS account to immediately halt billing.

### 2. S3 State Hydration
Because the worker nodes are constantly being deleted, the architecture is completely stateless. 
* When a user clicks "Launch" on the Next.js frontend, Django triggers an AWS Lambda function (`create_server`).
* Lambda provisions a fresh, blank Ubuntu EC2 instance and passes it a User-Data bootstrap script.
* During boot, the EC2 instance connects to your secure AWS S3 Backup Bucket, downloads the specific `world.zip` associated with that server name, and injects it into the Docker volume mount. 
* This allows the game state to seamlessly persist across infinite server creations and deletions.

### 3. Infrastructure as Code (IaC)
The entire foundational cloud network (VPCs, Subnets, Internet Gateways, IAM Roles, RDS Databases, and S3 Buckets) is managed exclusively through Terraform.
* **Remote State Management:** The `spin_up.sh` script dynamically creates a secure S3 bucket to store the `terraform.tfstate` file, ensuring the infrastructure deployment process is safe, tracked, and completely reproducible on any machine.
* **Dynamic Configuration:** Once Terraform successfully provisions the network, Boto3 passes the new database credentials and IPs to Ansible, which automatically SSHs into the Master EC2 node to configure the Django and Next.js Docker containers.

</details>