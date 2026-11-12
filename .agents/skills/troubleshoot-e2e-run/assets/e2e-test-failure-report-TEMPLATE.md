
# Title (E2E Test failure Report <runid>)
- Workflow run URL
- Date: (YYYY-MM-DD format)
- Summary: Number of failed jobs, total distinct failures, and brief primary cause
- A list of the failed job names.

## Overall Analysis Section
- **Summary table** with columns: Failure Type, Count, Actionable (with ✅/❌ indicators)
- **Likely Root Cause**: High-level synthesis connecting patterns across failures
- **Recommendations**: Numbered list with categories (Immediate, Investigation, etc.)
- **Closing assessment**: Whether failures are infrastructure, code, or test-related

## GitHub Actions Outage Section (conditional)
Include this section **only if** a GitHub service outage is confirmed during the test timeframe:
- Incident title and link to status page
- Official timeframe with UTC timestamps
- Impact severity and affected services
- Timeline correlation showing when observed failures occurred relative to the official incident
- Note any discrepancies (e.g., failures observed before official incident start time)

## Individual Failure Sections
For each test feature:
- **Job name and link** to the failed job
- **Status** with failure count
- For each PR failure within that job:
  - **Failure title**: PR number and brief description
  - **PR and Workflow links**
  - **Error**: Code block with the assertion or error message
  - **Root Cause**: Detailed technical explanation with timing, context, and what actually happened
  - **Impact**: Consequence of the failure (what didn't happen that should have)
  - **Remediation**: Specific, actionable steps (retry, investigate specific aspect, etc.)

## Style Guidelines
- Always use ASD-STE100 Technical English.
- Ensure consistent formatting of each individual failure section added.
- Include specific timestamps in UTC when relevant
- Link to all referenced PRs, workflows, and jobs
- Group related failures together
- Distinguish between transient infrastructure issues and code problems
- Be specific in remediation steps