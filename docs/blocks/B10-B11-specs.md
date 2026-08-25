# Block Specifications — B10 and B11 (entering AWS)

**Status**: Approved
**Created**: 2026-08-22 (REVIEW-001 finding M-9; renumbered from B6/B7 by ADR-017)
**Last updated**: 2026-08-25 (ADR-024: Elastic IP and the nightly shutdown; decisions separated
from worked examples)
**Related**: OPS-001, SEC-001, ARCH-001, ADR-005, ADR-014, **ADR-024**

> **How to read the values in this spec.** Two kinds of number appear here and they are not
> equally binding:
>
> - **Decisions** — marked **[DECIDED]**. Changing one changes cost, durability or the security
>   perimeter, and needs a reason written down. These are why this spec exists.
> - **Worked examples** — marked *[EXAMPLE]*. Sensible defaults chosen so the block reads as a
>   procedure rather than a puzzle. Adjust them at the console if reality differs; nothing
>   downstream depends on the exact value.
>
> Everything not marked is a step, not a value.

## Why these two blocks are specified in advance

`BLOCKS-001` says infrastructure blocks get more room because the target role is
Cloud/DevOps/SRE. Until this file existed, the opposite was true of the documentation: the
application blocks had full acceptance criteria while the infrastructure blocks had one line
each.

More importantly, **B10 and B11 are where irreversible spending starts.** Every earlier block
can be redone for free. From the moment B11 starts an instance, a clock runs. The most
detailed spec in this project belongs here, not in B4.

**Entry condition for B10: the B9 memory gate has passed.** If measured usage exceeded
1,250 MiB, `ARCH-001` is rewritten first. Do not create an AWS account to find out whether
the design fits.

---

## B10 — Account, identity and spending safety net

**Goal**: an AWS account exists that cannot quietly cost money, and every date that matters
is written down.

**Visible result**: three budget alarms configured, an IAM user with MFA, and a `STATUS.md`
section listing the account creation date and the credit expiry date.

### Tasks

1. **Check student programmes first.**
   - AWS Educate → sandboxed labs. Resources stop when the session ends.
   - AWS Academy Learner Lab → classroom account, session time limits, wiped at end of term.
   - **Neither can host this project.** Both are useful as a rehearsal environment for B11's
     console work — make your VPC mistakes there, for free, before doing it for real.
   - If any programme grants credits on a **real personal AWS account**, record the amount
     and expiry and revise the ARCH-001 cost model before continuing.
2. Create the AWS account with the **Paid plan** (OPS-001 §1 explains why not Free).
3. Root account: enable MFA, set a strong unique password, then **stop using root**.
   Record where the MFA recovery codes are stored (not in this repository).
4. Create an IAM user for daily work with MFA and an admin-scoped policy. Generate access
   keys only if a CLI is actually needed; prefer console + short-lived credentials.
5. Set the default region to `ap-northeast-2` (Seoul).
6. Enable **Cost Explorer** and set the billing alert email address. Enable
   "IAM user access to Billing information".
7. Create three **AWS Budgets** alarms at **$1, $5, $20** (OPS-001 §2). Setting up a budget
   is itself a credit-earning onboarding activity.
8. Complete the other onboarding activities that earn credits, and record the total credit
   amount received.
9. **Write the dates into `STATUS.md`:**
   - account creation date
   - credit amount
   - **credit expiry date** = creation + 12 months
   - "60 days before expiry" review date (OPS-001 §3)

### Acceptance criteria

- Root account is MFA-protected and has not been used since setup.
- The IAM user can log in with MFA and can see the Billing console.
- All three budget alarms exist and a test notification has been received at the alert email.
- `STATUS.md` contains the four dates above.
- **No compute resource exists yet.** B10 creates nothing that bills per hour.

### Cost created by this block

**$0/hour.** Nothing is running. This is the last block of which that is true.

### Not in this block

VPC, EC2, or anything with an hourly rate. Those are B11.

---

## B11 — Network and compute, by hand in the console

**Goal**: a server reachable over SSH, built by hand so that every layer is understood
before Terraform reproduces it in B15.

**Visible result**: `ssh ubuntu@<ip>` works, and `lsblk` shows a separate 10 GiB data volume
mounted at `/mnt/data`.

Per ADR-004 (DP-1), everything here is created manually in the console. The point is not
speed; B15 will make it reproducible. The point is knowing what Terraform is describing.

### Tasks

**1. VPC and networking**

| Resource | Value | Why |
|---|---|---|
| VPC CIDR *[EXAMPLE]* | `10.0.0.0/16` | Room to grow; no peering planned so any private range is fine |
| Public subnet *[EXAMPLE]* / **one AZ [DECIDED]** | `10.0.1.0/24` in `ap-northeast-2a` | The CIDR is arbitrary; **a single AZ is a decision** — there is one node, and the ADR-014 data volume is AZ-bound to it |
| Internet Gateway | attached to the VPC | |
| Route table | `0.0.0.0/0` → IGW, associated with the public subnet | |
| Auto-assign public IPv4 | enabled on the subnet | |

> **No NAT Gateway. [DECIDED]** The single node lives in a public subnet with a public IP. A NAT
> Gateway would cost ~$35/month — more than the entire budget — to solve a problem this
> architecture does not have (`CLAUDE.md` §5, OPS-001).

**2. Security group** — the whole perimeter, so write it out explicitly:

| Direction | Port | Protocol | Source / Destination | Purpose |
|---|---|---|---|---|
| Inbound | 22 | TCP | **your current IP /32** | SSH (SEC-8) |
| Inbound | 80 | TCP | `0.0.0.0/0` | HTTP → redirect + ACME HTTP-01 challenge |
| Inbound | 443 | TCP | `0.0.0.0/0` | HTTPS (Basic Auth behind it, SEC-1) |
| Outbound | all | all | `0.0.0.0/0` | Gmail API, ghcr.io, Let's Encrypt, S3, healthchecks.io |

**Not open**: 5432 (SEC-9), 6443 (kube-apiserver — reach it over SSH port-forward), and
anything else. The home IP changes; updating this rule is a normal chore, not a reason to
open 22 to the world.

**3. Key pair**

- Type `ed25519`. Download the private key and store it where the MFA recovery codes are
  **not** stored. Never in the repository.
- Record the fingerprint in `STATUS.md` so a future you can tell which key this is.

**3a. Elastic IP** — **[DECIDED]** (ADR-024)

Allocate **one** Elastic IP and associate it with the instance as soon as the instance exists.

The instance is stopped nightly by design (02:00–08:00 KST). **A stopped instance loses an
auto-assigned public IPv4 address and gets a different one on start**, which would break DNS,
TLS renewal, and every bookmark. The Elastic IP is what makes a nightly shutdown compatible with
a reachable, TLS-terminated site.

- **Cost: unchanged.** AWS bills every public IPv4 address at $0.005/hour whether it is
  auto-assigned or elastic. `ARCH-001` already carries the ~$3.7/month line.
- **Exactly one, always attached.** `CLAUDE.md` §5 and `OPS-001` §7's orphan check are about
  *unattached* addresses, which bill for nothing.
- Tags: `Project=schedule-manager`, `ManagedBy=console-b11`.

**4. EC2 instance**

| Setting | Value |
|---|---|
| AMI | Ubuntu Server 24.04 LTS, **arm64** |
| Instance type | `t4g.small` (2 vCPU, 2 GiB) |
| Subnet | the public subnet, auto-assign public IP |
| Root volume | gp3, **12 GiB** *[EXAMPLE size]*, delete-on-termination **true** **[DECIDED]** — it holds only reproducible things |
| Termination protection | **enabled** **[DECIDED]** |
| Detailed monitoring | off (costs money, VictoriaMetrics covers it from B17) |
| Tags | `Project=schedule-manager`, `ManagedBy=console-b11` |

The `ManagedBy` tag matters: in B15, anything still tagged `console-b11` is something
Terraform has not yet imported.

**5. Data volume (ADR-014)**

| Setting | Value |
|---|---|
| Type | gp3, **10 GiB** |
| AZ | same as the instance (`ap-northeast-2a`) |
| Delete on termination | **false** **[DECIDED]** — this is the entire point (ADR-014) |
| Device *[EXAMPLE]* | `/dev/sdf` — verify the in-guest name with `lsblk` |
| Tags | `Project=schedule-manager`, `Role=postgres-data` |

On the instance:

*[EXAMPLE — the commands below are a worked procedure, not a script to paste blind. Verify every
device name against `lsblk` on the actual instance.]*

```bash
sudo mkfs.ext4 /dev/nvme1n1          # verify the device name with lsblk first
sudo mkdir -p /mnt/data
# mount by UUID, never by device name — device names are not stable across reboots
sudo blkid /dev/nvme1n1
echo 'UUID=<uuid>  /mnt/data  ext4  defaults,nofail  0  2' | sudo tee -a /etc/fstab
sudo mount -a
```

**`nofail` and mounting by UUID are [DECIDED], not stylistic.** Device names are not stable
across reboots, and without `nofail` a missing volume makes the instance fail to boot into a
state you can SSH into — during an incident, on a node you cannot reach.

**6. Harden and verify**

- `PasswordAuthentication no` in `/etc/ssh/sshd_config` (SEC-8), reload sshd.
- `sudo unattended-upgrades` enabled for security updates.
- Confirm the instance is reachable and `df -h /mnt/data` shows the mounted volume.
- **Reboot once** and confirm `/mnt/data` comes back automatically. An fstab entry that only
  works until the first reboot is a trap that surfaces during a real incident.

### Acceptance criteria

- `ssh -i <key> ubuntu@<public-ip>` succeeds; password auth is refused.
- SSH from any IP other than the allowed one times out.
- `lsblk` shows a 10 GiB volume mounted at `/mnt/data`, and it survives a reboot.
- The data volume's "delete on termination" is **false** — verify in the console, do not
  assume.
- Termination protection is enabled on the instance.
- No NAT Gateway and no load balancer exists in the account.
- **Exactly one Elastic IP exists, and it is associated with the instance** (ADR-024). An
  unattached one is a defect — it bills for nothing and is on the monthly orphan check.
- **Stop the instance once and start it again**, and confirm the address is unchanged. This is
  the property the Elastic IP exists for, and it is invisible until the first nightly shutdown.
- `STATUS.md` records: instance id, volume ids, **Elastic IP allocation id and address**, key
  fingerprint, AZ.

### Cost created by this block

**About $0.029/hour while running → roughly $16/month once the nightly shutdown is in place**
(`t4g.small` ~$0.021/hr Seoul for 18 h/day + 22 GiB gp3 + the Elastic IP at ~$0.005/hr, which
bills 24×7 regardless). Without the shutdown it is ~$21/month.

**From this block onward the project costs money continuously.** Charged against credits until
they expire (OPS-001 §1). Write that sentence into the block summary in `STATUS.md`.

> **The shutdown schedule itself is not built here.** ADR-024 requires it to live **outside** the
> instance — a cron entry on the node cannot start the node. Decide the mechanism (an EventBridge
> scheduled rule calling `StopInstances`/`StartInstances`, or equivalent) at B13, when the
> collector's 08:05 run is also being scheduled. Until then, stop the instance by hand when it is
> not in use; the cost figures above assume the schedule exists.

### Not in this block

k3s, ingress, TLS, and anything running in the cluster. Those are B12.

---

## Rehearsal note

If an AWS Educate or Academy lab is available, do a dry run of B11 there first: build the VPC,
launch an instance, attach a second volume, mount it, break it, and start over. Lab resources
are wiped anyway, so mistakes are free. Then do it once, carefully, in the real account.

This is the cheapest risk reduction available in the whole roadmap.
