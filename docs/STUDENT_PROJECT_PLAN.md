# CloudConnect Fargate Student Project Plan

Students build and run a production-style microservices app locally with Docker, then map it to AWS ECS Fargate.

## Local services

- Frontend: React + Nginx
- Auth Service: registration, login, JWT
- User Service: profile and bio
- Post Service: post creation and feed
- Like Service: post like/unlike
- Comment Service: comments with optional public images and comment likes
- Analytics Service: reads PostgreSQL and shows users, posts, impressions, engagement, daily activity, and top posts
- PostgreSQL: shared local database

## Learning goals

1. Understand microservices and container boundaries.
2. Run a multi-container application with Docker Compose.
3. Debug service failures using logs, health checks, and container status.
4. Understand local Nginx path routing as a preview of AWS ALB path-based routing.
5. Map local containers to ECS Fargate services, ECR repositories, CloudWatch logs, and RDS PostgreSQL.
6. Explain cloud security using private subnets, security groups, JWT, Secrets Manager, and private database connectivity.

## Recommended student checkpoints

- App opens on `http://localhost:3000`.
- All service health checks return OK.
- Registration and login work.
- Post creation, post like, comments with optional public images, and comment likes work.
- Analytics page shows metrics from PostgreSQL.
- Students can explain how `502 Bad Gateway`, `500 Internal Server Error`, and missing dependency errors are diagnosed.


## Optional Public Image Rendering

The Post Service and Comment Service support an optional `image_url` field. When a user provides a public `http://` or `https://` image URL, the React feed renders that image below the post or comment text. If no image URL is provided, the app behaves like a normal text-only feed. This teaches students how APIs, database schema, frontend forms, and rendering logic evolve together.

## Redis Queue Extension

Post creation now demonstrates asynchronous processing. The Post Service accepts a post request, stores a `post_jobs` row, pushes a `post.create.requested` event to Redis Queue, and returns a job id. The Worker Service consumes the queue, inserts the final post into PostgreSQL, updates the job status, and updates Redis queue metrics. The frontend intentionally shows a 2-second animated loader so students can see the difference between synchronous database writes and queue-backed background processing.
