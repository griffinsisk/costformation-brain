# My Organization — Business Context

Freeform notes about your organization that help the agent make better decisions when writing CostFormation. Fill in what's relevant — skip what isn't.

## Organization Structure

<!-- How is your engineering org structured? Teams, business units, products? -->
<!-- Example: "3 product lines (Core, Analytics, Billing), each with 2-4 teams. Platform team is shared." -->

## Cloud Footprint

<!-- Which cloud providers? How many accounts? Any multi-cloud? -->
<!-- Example: "AWS only, 45 accounts across 3 org units (Production, Non-Prod, Shared Services)" -->

## What Are You Trying to See?

<!-- What cost views matter to your business? Who are the audiences? -->
<!-- Example: "VP Eng wants cost per team per month. CFO wants cost per product. SRE wants cost per environment." -->

## Shared Resources

<!-- What infrastructure is shared across teams/products? How should costs be split? -->
<!-- Example: "Shared RDS cluster, shared EKS cluster, shared S3 data lake. Split by usage where possible, proportional otherwise." -->

## Tagging Maturity

<!-- How consistent is your tagging? Any known gaps? -->
<!-- Example: "Good on EKS (admission webhook enforces), spotty on EC2 (legacy instances), no tags on networking resources." -->

## Telemetry Readiness

<!-- Do you have usage signals you can send to CloudZero? Or would you prefer rules-based allocation? -->
<!-- Example: "We have per-customer request counts in Datadog. No other telemetry yet." -->

## Constraints or Preferences

<!-- Anything the agent should know about how you want dimensions designed? -->
<!-- Example: "Keep it simple — we'd rather have 5 accurate dimensions than 20 approximate ones." -->
<!-- Example: "We need to match our internal JIRA team names exactly for chargeback." -->
