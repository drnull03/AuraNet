# Build Stage
FROM golang:1.22-alpine AS builder

WORKDIR /app

# Copy module files and download dependencies
COPY go.mod go.sum* ./
RUN go mod download

# Copy the source code and build the binary
COPY main.go .
RUN CGO_ENABLED=0 GOOS=linux go build -o loan-service main.go

# Final Stage (Tiny Image)
FROM alpine:latest
RUN apk --no-cache add ca-certificates

WORKDIR /root/
COPY --from=builder /app/loan-service .

EXPOSE 8081

CMD ["./loan-service"]
