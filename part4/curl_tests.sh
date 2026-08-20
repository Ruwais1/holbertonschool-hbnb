#!/usr/bin/env bash
# Authenticated black-box tests for the Part 4 API.
set -u

BASE_URL="${BASE_URL:-http://127.0.0.1:5000/api/v1}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@hbnb.io}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin1234}"
PASS=0
FAIL=0
LAST_BODY=""
LAST_STATUS=""

call_api() {
    local method="$1"
    local path="$2"
    local data="${3-}"
    local token="${4-}"
    local body_file
    local args=(-sS -o "")
    body_file="$(mktemp)"
    args=(-sS -o "$body_file" -w "%{http_code}" -X "$method")

    if [[ -n "$data" ]]; then
        args+=(-H "Content-Type: application/json" -d "$data")
    fi
    if [[ -n "$token" ]]; then
        args+=(-H "Authorization: Bearer ${token}")
    fi

    LAST_STATUS="$(curl "${args[@]}" "${BASE_URL}${path}")"
    LAST_BODY="$(<"$body_file")"
    rm -f "$body_file"
}

expect_status() {
    local label="$1"
    local expected="$2"
    if [[ "$LAST_STATUS" == "$expected" ]]; then
        printf 'PASS  %-52s HTTP %s\n' "$label" "$LAST_STATUS"
        PASS=$((PASS + 1))
    else
        printf 'FAIL  %-52s expected %s, got %s\n' \
            "$label" "$expected" "$LAST_STATUS"
        printf '      Response: %s\n' "$LAST_BODY"
        FAIL=$((FAIL + 1))
    fi
}

json_value() {
    local field="$1"
    printf '%s\n' "$LAST_BODY" |
        sed -n "s/.*\"${field}\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" |
        head -n 1
}

suffix="$(date +%s)"

call_api GET "/"
expect_status "Swagger UI is available" 200

call_api POST "/auth/login" \
    "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}"
expect_status "Seeded administrator can log in" 200
ADMIN_TOKEN="$(json_value access_token)"

call_api POST "/users/" \
    "{\"first_name\":\"Owner\",\"last_name\":\"One\",\"email\":\"owner.${suffix}@example.com\",\"password\":\"ownerpass\"}" \
    "$ADMIN_TOKEN"
expect_status "Admin creates an owner" 201
OWNER_ID="$(json_value id)"

call_api POST "/users/" \
    "{\"first_name\":\"Reviewer\",\"last_name\":\"Two\",\"email\":\"reviewer.${suffix}@example.com\",\"password\":\"reviewpass\"}" \
    "$ADMIN_TOKEN"
expect_status "Admin creates a reviewer" 201
REVIEWER_ID="$(json_value id)"

call_api POST "/auth/login" \
    "{\"email\":\"owner.${suffix}@example.com\",\"password\":\"ownerpass\"}"
expect_status "Owner can log in with hashed password" 200
OWNER_TOKEN="$(json_value access_token)"

call_api POST "/auth/login" \
    "{\"email\":\"reviewer.${suffix}@example.com\",\"password\":\"reviewpass\"}"
expect_status "Reviewer can log in with hashed password" 200
REVIEWER_TOKEN="$(json_value access_token)"

call_api POST "/users/" \
    '{"first_name":"Blocked","last_name":"User","email":"blocked@example.com","password":"pass"}' \
    "$OWNER_TOKEN"
expect_status "Regular user cannot create users" 403

call_api PUT "/users/${OWNER_ID}" \
    '{"email":"forbidden@example.com"}' "$OWNER_TOKEN"
expect_status "Regular user cannot modify email" 400

call_api POST "/users/" \
    '{"first_name":"","last_name":"Doe","email":"invalid-email","password":"pass"}' \
    "$ADMIN_TOKEN"
expect_status "Invalid user data is rejected" 400

call_api POST "/amenities/" "{\"name\":\"Sauna ${suffix}\"}" "$ADMIN_TOKEN"
expect_status "Admin creates an amenity" 201
AMENITY_ID="$(json_value id)"

call_api POST "/amenities/" '{"name":"Blocked amenity"}' "$OWNER_TOKEN"
expect_status "Regular user cannot create amenities" 403

call_api POST "/places/" \
    "{\"title\":\"Seaside Apartment\",\"description\":\"Near the beach\",\"price\":150,\"latitude\":24.7136,\"longitude\":46.6753,\"amenities\":[\"${AMENITY_ID}\"]}" \
    "$OWNER_TOKEN"
expect_status "Owner creates a place" 201
PLACE_ID="$(json_value id)"

call_api POST "/places/" \
    '{"title":"Free Place","price":0,"latitude":0,"longitude":0}' \
    "$OWNER_TOKEN"
expect_status "Non-positive place price is rejected" 400

call_api PUT "/places/${PLACE_ID}" '{"title":"Hacked"}' "$REVIEWER_TOKEN"
expect_status "Non-owner cannot update a place" 403

call_api POST "/reviews/" \
    "{\"text\":\"Invalid rating\",\"rating\":6,\"place_id\":\"${PLACE_ID}\"}" \
    "$REVIEWER_TOKEN"
expect_status "Out-of-range review rating is rejected" 400

call_api POST "/reviews/" \
    "{\"text\":\"Excellent stay\",\"rating\":5,\"place_id\":\"${PLACE_ID}\"}" \
    "$REVIEWER_TOKEN"
expect_status "Reviewer creates a review" 201
REVIEW_ID="$(json_value id)"

call_api PUT "/reviews/${REVIEW_ID}" \
    '{"text":"Updated review","rating":4}' "$OWNER_TOKEN"
expect_status "Non-author cannot update a review" 403

call_api PUT "/reviews/${REVIEW_ID}" \
    '{"text":"Updated review","rating":4}' "$REVIEWER_TOKEN"
expect_status "Author updates a review" 200

call_api DELETE "/reviews/${REVIEW_ID}" "" "$REVIEWER_TOKEN"
expect_status "Author deletes a review" 200

call_api GET "/reviews/${REVIEW_ID}"
expect_status "Deleted review is no longer available" 404

printf '\nSummary: %s passed, %s failed\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]
