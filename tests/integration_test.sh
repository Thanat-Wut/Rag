#!/bin/bash

################################################################################
# WUT-WAY Integration Test Script
# 
# Tests the integration between WUT (Thanat-Wut/Rag) and WAY (Waytid-way/Rag_way)
# 
# Prerequisites:
#   - docker-compose up -d (all services running)
#   - jq installed (sudo apt-get install jq)
#   - curl installed
#
# Usage:
#   ./integration_test.sh                    # Run all tests
#   ./integration_test.sh --verbose          # Run with detailed output
#   ./integration_test.sh --service wut      # Test only WUT service
#   ./integration_test.sh --service way      # Test only WAY service
################################################################################

set -e  # Exit on error

# ============================================================================
# Configuration
# ============================================================================
WUT_URL="${WUT_URL:-http://localhost:8001}"
WAY_URL="${WAY_URL:-http://localhost:8000}"
QDRANT_URL="${QDRANT_URL:-http://localhost:6333}"

VERBOSE=0
SERVICE="all"
LOG_FILE="tests/integration_test.log"
RESULTS_FILE="tests/test_results.json"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# ============================================================================
# Helper Functions
# ============================================================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$LOG_FILE"
    ((PASSED_TESTS++))
}

fail() {
    echo -e "${RED}✗${NC} $1" | tee -a "$LOG_FILE"
    ((FAILED_TESTS++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1" | tee -a "$LOG_FILE"
}

test_start() {
    ((TOTAL_TESTS++))
    log "Test $TOTAL_TESTS: $1"
}

# ============================================================================
# Service Health Checks
# ============================================================================

check_service_health() {
    local service_name=$1
    local url=$2
    local endpoint=$3
    
    test_start "Health check for $service_name"
    
    response=$(curl -s -w "\n%{http_code}" "${url}${endpoint}" 2>&1)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [[ "$http_code" == "200" ]]; then
        success "$service_name is healthy"
        [[ $VERBOSE -eq 1 ]] && echo "Response: $body"
        return 0
    else
        fail "$service_name health check failed (HTTP $http_code)"
        [[ $VERBOSE -eq 1 ]] && echo "Response: $body"
        return 1
    fi
}

# ============================================================================
# WUT Service Tests
# ============================================================================

test_wut_health() {
    check_service_health "WUT Backend" "$WUT_URL" "/health"
}

test_wut_root() {
    test_start "WUT root endpoint"
    
    response=$(curl -s -w "\n%{http_code}" "${WUT_URL}/" 2>&1)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [[ "$http_code" == "200" ]] && echo "$body" | jq -e '.service == "WUT Backend"' > /dev/null 2>&1; then
        success "WUT root endpoint responds correctly"
        [[ $VERBOSE -eq 1 ]] && echo "$body" | jq '.'
    else
        fail "WUT root endpoint failed"
        [[ $VERBOSE -eq 1 ]] && echo "Response: $body"
    fi
}

test_wut_query_simple() {
    test_start "WUT simple query"
    
    payload='{
        "message": "How do I reset my password?",
        "department": "IT",
        "trace_id": "test-simple-001"
    }'
    
    response=$(curl -s -w "\n%{http_code}" -X POST "${WUT_URL}/api/query" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>&1)
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [[ "$http_code" == "200" ]]; then
        # Validate required fields
        if echo "$body" | jq -e '.reply and .confidence and .action and .trace_id' > /dev/null 2>&1; then
            success "WUT simple query successful"
            
            confidence=$(echo "$body" | jq -r '.confidence')
            action=$(echo "$body" | jq -r '.action')
            
            [[ $VERBOSE -eq 1 ]] && {
                echo "  Confidence: $confidence"
                echo "  Action: $action"
                echo "$body" | jq '.'
            }
        else
            fail "WUT response missing required fields"
            [[ $VERBOSE -eq 1 ]] && echo "$body" | jq '.'
        fi
    else
        fail "WUT query failed (HTTP $http_code)"
        [[ $VERBOSE -eq 1 ]] && echo "Response: $body"
    fi
}

test_wut_query_urgent() {
    test_start "WUT urgent query detection"
    
    payload='{
        "message": "URGENT: My computer crashed and I lost all data!",
        "department": "IT",
        "trace_id": "test-urgent-002"
    }'
    
    response=$(curl -s -w "\n%{http_code}" -X POST "${WUT_URL}/api/query" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>&1)
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [[ "$http_code" == "200" ]]; then
        has_urgent=$(echo "$body" | jq -r '.business_signals.has_urgent_keywords')
        has_action=$(echo "$body" | jq -r '.business_signals.has_action_keywords')
        
        if [[ "$has_urgent" == "true" ]] && [[ "$has_action" == "true" ]]; then
            success "WUT correctly detected urgent query"
            [[ $VERBOSE -eq 1 ]] && echo "$body" | jq '.business_signals'
        else
            fail "WUT failed to detect urgent keywords (urgent=$has_urgent, action=$has_action)"
        fi
    else
        fail "WUT urgent query failed (HTTP $http_code)"
    fi
}

test_wut_query_hr() {
    test_start "WUT HR department query"
    
    payload='{
        "message": "How many days of annual leave do I have?",
        "department": "HR",
        "trace_id": "test-hr-003"
    }'
    
    response=$(curl -s -w "\n%{http_code}" -X POST "${WUT_URL}/api/query" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>&1)
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [[ "$http_code" == "200" ]]; then
        dept_match=$(echo "$body" | jq -r '.business_signals.query_department_match')
        
        if [[ "$dept_match" == "true" ]]; then
            success "WUT correctly matched HR department"
        else
            warn "WUT did not match department (this may be expected if WAY classifies differently)"
        fi
        
        [[ $VERBOSE -eq 1 ]] && echo "$body" | jq '{reply, confidence, business_signals}'
    else
        fail "WUT HR query failed (HTTP $http_code)"
    fi
}

test_wut_invalid_payload() {
    test_start "WUT invalid payload handling"
    
    payload='{"invalid": "payload"}'
    
    response=$(curl -s -w "\n%{http_code}" -X POST "${WUT_URL}/api/query" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>&1)
    
    http_code=$(echo "$response" | tail -n1)
    
    if [[ "$http_code" == "422" ]]; then
        success "WUT correctly rejected invalid payload"
    else
        fail "WUT should return 422 for invalid payload (got $http_code)"
    fi
}

# ============================================================================
# WAY Service Tests
# ============================================================================

test_way_health() {
    check_service_health "WAY Backend" "$WAY_URL" "/health"
}

test_way_root() {
    test_start "WAY root endpoint"
    
    response=$(curl -s -w "\n%{http_code}" "${WAY_URL}/" 2>&1)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [[ "$http_code" == "200" ]]; then
        success "WAY root endpoint responds"
        [[ $VERBOSE -eq 1 ]] && echo "$body" | jq '.'
    else
        fail "WAY root endpoint failed (HTTP $http_code)"
    fi
}

test_way_rag_query() {
    test_start "WAY RAG query endpoint"
    
    payload='{
        "query": "What is the password reset policy?",
        "trace_id": "test-way-001",
        "user_dept": "IT"
    }'
    
    response=$(curl -s -w "\n%{http_code}" -X POST "${WAY_URL}/rag/query" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>&1)
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [[ "$http_code" == "200" ]]; then
        if echo "$body" | jq -e '.answer and .rag_confidence' > /dev/null 2>&1; then
            success "WAY RAG query successful"
            
            rag_confidence=$(echo "$body" | jq -r '.rag_confidence')
            [[ $VERBOSE -eq 1 ]] && {
                echo "  RAG Confidence: $rag_confidence"
                echo "$body" | jq '{answer, rag_confidence, suggested_action}'
            }
        else
            fail "WAY response missing required fields"
        fi
    else
        fail "WAY RAG query failed (HTTP $http_code)"
        [[ $VERBOSE -eq 1 ]] && echo "Response: $body"
    fi
}

# ============================================================================
# Qdrant Service Tests
# ============================================================================

test_qdrant_health() {
    check_service_health "Qdrant" "$QDRANT_URL" "/health"
}

test_qdrant_collections() {
    test_start "Qdrant collections check"
    
    response=$(curl -s -w "\n%{http_code}" "${QDRANT_URL}/collections" 2>&1)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [[ "$http_code" == "200" ]]; then
        success "Qdrant collections endpoint accessible"
        [[ $VERBOSE -eq 1 ]] && echo "$body" | jq '.'
    else
        fail "Qdrant collections check failed (HTTP $http_code)"
    fi
}

# ============================================================================
# Integration Tests (WUT + WAY)
# ============================================================================

test_end_to_end_flow() {
    test_start "End-to-end query flow (WUT → WAY → Qdrant)"
    
    payload='{
        "message": "How do I submit an expense claim?",
        "department": "Accounting",
        "trace_id": "test-e2e-001",
        "max_results": 3
    }'
    
    response=$(curl -s -w "\n%{http_code}" -X POST "${WUT_URL}/api/query" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>&1)
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [[ "$http_code" == "200" ]]; then
        # Check that all components contributed
        has_reply=$(echo "$body" | jq -e '.reply' > /dev/null 2>&1 && echo "true" || echo "false")
        has_confidence=$(echo "$body" | jq -e '.confidence' > /dev/null 2>&1 && echo "true" || echo "false")
        has_docs=$(echo "$body" | jq -e '.retrieved_docs' > /dev/null 2>&1 && echo "true" || echo "false")
        has_debug=$(echo "$body" | jq -e '.debug_info' > /dev/null 2>&1 && echo "true" || echo "false")
        
        if [[ "$has_reply" == "true" ]] && [[ "$has_confidence" == "true" ]] && \
           [[ "$has_docs" == "true" ]] && [[ "$has_debug" == "true" ]]; then
            success "End-to-end flow completed successfully"
            
            num_docs=$(echo "$body" | jq '.retrieved_docs | length')
            latency=$(echo "$body" | jq -r '.debug_info.latency_breakdown.total_ms')
            
            [[ $VERBOSE -eq 1 ]] && {
                echo "  Retrieved docs: $num_docs"
                echo "  Total latency: ${latency}ms"
                echo "$body" | jq '{reply, confidence, action, citations, debug_info}'
            }
        else
            fail "End-to-end flow incomplete (reply=$has_reply, confidence=$has_confidence, docs=$has_docs, debug=$has_debug)"
        fi
    else
        fail "End-to-end flow failed (HTTP $http_code)"
        [[ $VERBOSE -eq 1 ]] && echo "Response: $body"
    fi
}

# ============================================================================
# Performance Tests
# ============================================================================

test_response_time() {
    test_start "Response time performance"
    
    payload='{
        "message": "Test query for performance",
        "trace_id": "test-perf-001"
    }'
    
    start_time=$(date +%s%N)
    response=$(curl -s -w "\n%{http_code}" -X POST "${WUT_URL}/api/query" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>&1)
    end_time=$(date +%s%N)
    
    elapsed_ms=$(( (end_time - start_time) / 1000000 ))
    http_code=$(echo "$response" | tail -n1)
    
    if [[ "$http_code" == "200" ]]; then
        # Threshold: 5000ms (5 seconds)
        if [[ $elapsed_ms -lt 5000 ]]; then
            success "Response time acceptable: ${elapsed_ms}ms"
        else
            warn "Response time slow: ${elapsed_ms}ms (threshold: 5000ms)"
        fi
    else
        fail "Performance test failed (HTTP $http_code)"
    fi
}

# ============================================================================
# Main Test Runner
# ============================================================================

run_tests() {
    local service=$1
    
    log "========================================"
    log "WUT-WAY Integration Test Suite"
    log "========================================"
    log "WUT URL: $WUT_URL"
    log "WAY URL: $WAY_URL"
    log "Qdrant URL: $QDRANT_URL"
    log "Verbose: $VERBOSE"
    log "Service: $service"
    log "========================================"
    echo ""
    
    # Clear log file
    > "$LOG_FILE"
    
    case $service in
        "wut")
            log "Running WUT tests only..."
            test_wut_health
            test_wut_root
            test_wut_query_simple
            test_wut_query_urgent
            test_wut_query_hr
            test_wut_invalid_payload
            ;;
        "way")
            log "Running WAY tests only..."
            test_way_health
            test_way_root
            test_way_rag_query
            ;;
        "qdrant")
            log "Running Qdrant tests only..."
            test_qdrant_health
            test_qdrant_collections
            ;;
        "all"|*)
            log "Running all tests..."
            
            # Health checks first
            log "=== Health Checks ==="
            test_qdrant_health
            test_way_health
            test_wut_health
            echo ""
            
            # Basic endpoint tests
            log "=== Basic Endpoints ==="
            test_qdrant_collections
            test_way_root
            test_wut_root
            echo ""
            
            # Functional tests
            log "=== Functional Tests ==="
            test_way_rag_query
            test_wut_query_simple
            test_wut_query_urgent
            test_wut_query_hr
            test_wut_invalid_payload
            echo ""
            
            # Integration tests
            log "=== Integration Tests ==="
            test_end_to_end_flow
            echo ""
            
            # Performance tests
            log "=== Performance Tests ==="
            test_response_time
            ;;
    esac
    
    echo ""
    log "========================================"
    log "Test Results"
    log "========================================"
    log "Total tests: $TOTAL_TESTS"
    log "Passed: ${GREEN}$PASSED_TESTS${NC}"
    log "Failed: ${RED}$FAILED_TESTS${NC}"
    log "Success rate: $(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")%"
    log "========================================"
    
    # Save results to JSON
    cat > "$RESULTS_FILE" <<EOF
{
    "timestamp": "$(date -Iseconds)",
    "total": $TOTAL_TESTS,
    "passed": $PASSED_TESTS,
    "failed": $FAILED_TESTS,
    "success_rate": $(awk "BEGIN {printf \"%.2f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}"),
    "service": "$service",
    "log_file": "$LOG_FILE"
}
EOF
    
    log "Results saved to: $RESULTS_FILE"
    log "Full log saved to: $LOG_FILE"
    
    # Exit with failure if any tests failed
    [[ $FAILED_TESTS -gt 0 ]] && exit 1
    exit 0
}

# ============================================================================
# Parse Arguments
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=1
            shift
            ;;
        --service|-s)
            SERVICE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --verbose, -v         Enable verbose output"
            echo "  --service, -s SERVICE Test specific service (wut|way|qdrant|all)"
            echo "  --help, -h            Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  WUT_URL      WUT service URL (default: http://localhost:8001)"
            echo "  WAY_URL      WAY service URL (default: http://localhost:8000)"
            echo "  QDRANT_URL   Qdrant URL (default: http://localhost:6333)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# ============================================================================
# Run Tests
# ============================================================================

run_tests "$SERVICE"
