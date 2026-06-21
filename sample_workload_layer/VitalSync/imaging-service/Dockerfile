# Build Stage
FROM golang:1.22-alpine AS builder

WORKDIR /app

# Initialize a go module dynamically for our single-file app
RUN go mod init vitalsync/imaging-service

# Copy the source code and build the binary
COPY main.go .
RUN CGO_ENABLED=0 GOOS=linux go build -o imaging-service main.go

# Final Stage (Tiny Image)
# We use alpine so that the /etc/passwd file actually exists for our LFI demo!
FROM alpine:latest
RUN apk --no-cache add ca-certificates

WORKDIR /root/
COPY --from=builder /app/imaging-service .

EXPOSE 8081

CMD ["./imaging-service"]
