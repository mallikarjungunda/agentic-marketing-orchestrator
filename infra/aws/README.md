# AWS deployment milestone

No cloud resources are provisioned by this starter. Before public deployment, implement identity-based authentication, role-bound approvals, migrations and a durable worker.

Suggested future layout: containerized web/API/worker on ECS Fargate; private RDS PostgreSQL; SQS job queue; Secrets Manager; CloudWatch; HTTPS load balancer. Start with a cost estimate and create staging infrastructure through CDK. Do not deploy the unauthenticated demo UI publicly.
