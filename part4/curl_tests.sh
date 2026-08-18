#!/usr/bin/env bash
# Manual black-box tests for the HBnB API.
# Start the server first with: python3 run.py
set -u

BASE_URL="${BASE_URL:-http://127.0.0.1:5000/api/v1}"
PASS=0
FAIL=0
LAST_BODY=""
LAST_STATUS=""

call_api() {
    local method="$1"
    local path="$2"
    local data="${3-}"
    local body_file
    body_file="$(mktemp)"

    if [[ -n "$data" ]]; then
        LAST_STATUS="$(curl -sS -o "$body_file" -w "%{http_code}" \
            -X "$method" "${BASE_URL}${path}" \
            -H "Content-Type: application/json" \
            -d "$data")"
    else
        LAST_STATUS="$(curl -sS -o "$body_file" -w "%{http_code}" \
            -X "$method" "${BASE_URL}${path}")"
    fi

    LAST_BODY="$(cat "$body_file")"
    rm -f "$body_file"
}

expect_status() {
    local label="$1"
    local expected="$2"

    if [[ "$LAST_STATUS" == "$expected" ]]; then
        printf 'PASS  %-46s HTTP %s\n' "$label" "$LAST_STATUS"
        PASS=$((PASS + 1))
    else
        printf 'FAIL  %-46s expected %s, got %s\n' \
            "$label" "$expected" "$LAST_STATUS"
        printf '      Response: %s\n' "$LAST_BODY"
        FAIL=$((FAIL + 1))
    fi
}

json_id() {
    printf '%s\n' "$LAST_BODY" |
        grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' |
        head -n 1 |
        cut -d '"' -f 4
}

suffix="$(date +%s)"

# Wait briefly for a locally-started development server.
for _ in $(seq 1 20); do
    call_api GET "/"
    if [[ "$LAST_STATUS" != "000" ]]; then
        break
    fi
    sleep 0.5
done
expect_status "Swagger UI is available" 200

call_api POST "/users/" \
    "{\"first_name\":\"Owner\",\"last_name\":\"One\",\"email\":\"owner.${suffix}@example.com\"}"
expect_status "Create a valid owner" 201
OWNER_ID="$(json_id)"

call_api POST "/users/" \
    '{"first_name":"","last_name":"Doe","email":"invalid-email"}'
expect_status "Reject invalid user data" 400

call_api POST "/users/" \
    "{\"first_name\":\"Reviewer\",\"last_name\":\"Two\",\"email\":\"reviewer.${suffix}@example.com\"}"
expect_status "Create a valid reviewer" 201
REVIEWER_ID="$(json_id)"

call_api POST "/amenities/" '{"name":"Wi-Fi"}'
expect_status "Create a valid amenity" 201
AMENITY_ID="$(json_id)"

call_api POST "/amenities/" '{"name":""}'
expect_status "Reject an empty amenity name" 400

call_api POST "/places/" \
    "{\"title\":\"Seaside Apartment\",\"description\":\"Near the beach\",\"price\":150,\"latitude\":24.7136,\"longitude\":46.6753,\"owner_id\":\"${OWNER_ID}\",\"amenities\":[\"${AMENITY_ID}\"]}"
expect_status "Create a valid place" 201
PLACE_ID="$(json_id)"

call_api POST "/places/" \
    "{\"title\":\"Free Place\",\"price\":0,\"latitude\":0,\"longitude\":0,\"owner_id\":\"${OWNER_ID}\"}"
expect_status "Reject a non-positive price" 400

call_api POST "/places/" \
    "{\"title\":\"Invalid Coordinates\",\"price\":100,\"latitude\":91,\"longitude\":0,\"owner_id\":\"${OWNER_ID}\"}"
expect_status "Reject out-of-range latitude" 400

call_api POST "/reviews/" \
    "{\"text\":\"Excellent stay\",\"rating\":5,\"user_id\":\"${REVIEWER_ID}\",\"place_id\":\"${PLACE_ID}\"}"
expect_status "Create a valid review" 201
REVIEW_ID="$(json_id)"

call_api POST "/reviews/" \
    "{\"text\":\"Bad rating\",\"rating\":6,\"user_id\":\"${OWNER_ID}\",\"place_id\":\"${PLACE_ID}\"}"
expect_status "Reject a rating outside 1-5" 400

call_api GET "/places/not-a-real-id"
expect_status "Return 404 for a missing place" 404

call_api GET "/places/${PLACE_ID}/reviews"
expect_status "List reviews for a place" 200

call_api PUT "/reviews/${REVIEW_ID}" \
    '{"text":"Updated review","rating":4}'
expect_status "Update a review" 200

call_api DELETE "/reviews/${REVIEW_ID}"
expect_status "Delete a review" 200

printf '\nSummary: %s passed, %s failed\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]
