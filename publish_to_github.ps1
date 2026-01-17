# PowerShell Script to Publish to GitHub
# Run this script from the project directory

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Publishing to GitHub" -ForegroundColor Cyan
Write-Host "Repository: cloudbadal007/ontology-mcp-self-healing" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Initialize Git (if not already done)
Write-Host "Step 1: Initializing Git repository..." -ForegroundColor Yellow
if (Test-Path .git) {
    Write-Host "  ✓ Git repository already initialized" -ForegroundColor Green
} else {
    git init
    Write-Host "  ✓ Git repository initialized" -ForegroundColor Green
}

# Step 2: Check .gitignore
Write-Host "`nStep 2: Verifying .gitignore..." -ForegroundColor Yellow
if (Test-Path .gitignore) {
    Write-Host "  ✓ .gitignore exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ .gitignore not found!" -ForegroundColor Red
    exit 1
}

# Step 3: Add all files
Write-Host "`nStep 3: Adding files to Git..." -ForegroundColor Yellow
git add .
Write-Host "  ✓ Files added" -ForegroundColor Green

# Step 4: Check status
Write-Host "`nStep 4: Checking status..." -ForegroundColor Yellow
git status --short

# Step 5: Create commit
Write-Host "`nStep 5: Creating initial commit..." -ForegroundColor Yellow
$commitMessage = @"
Initial commit: Self-healing ontology MCP agent system

- Complete self-healing multi-agent system
- MCP server with ontology-based tool generation
- Schema monitoring and automatic healing
- Comprehensive test suite (13 test files)
- Docker support with docker-compose
- Full documentation (README, setup guide, architecture docs)
- CI/CD workflow configured
"@

git commit -m $commitMessage
Write-Host "  ✓ Commit created" -ForegroundColor Green

# Step 6: Set branch to main
Write-Host "`nStep 6: Setting branch to main..." -ForegroundColor Yellow
git branch -M main
Write-Host "  ✓ Branch set to main" -ForegroundColor Green

# Step 7: Add remote
Write-Host "`nStep 7: Adding GitHub remote..." -ForegroundColor Yellow
$remoteUrl = "https://github.com/cloudbadal007/ontology-mcp-self-healing.git"

# Check if remote already exists
$remotes = git remote -v
if ($remotes -match "cloudbadal007") {
    Write-Host "  ✓ Remote already exists" -ForegroundColor Green
    git remote set-url origin $remoteUrl
} else {
    git remote add origin $remoteUrl
    Write-Host "  ✓ Remote added: $remoteUrl" -ForegroundColor Green
}

# Step 8: Instructions for manual steps
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Next Steps (Manual):" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Create repository on GitHub:" -ForegroundColor Yellow
Write-Host "   Go to: https://github.com/new" -ForegroundColor White
Write-Host "   Repository name: ontology-mcp-self-healing" -ForegroundColor White
Write-Host "   Description: Self-healing multi-agent system using ontologies and MCP" -ForegroundColor White
Write-Host "   Visibility: Public (or Private)" -ForegroundColor White
Write-Host "   DO NOT initialize with README, .gitignore, or license" -ForegroundColor White
Write-Host "   Click 'Create repository'" -ForegroundColor White
Write-Host ""
Write-Host "2. Push to GitHub:" -ForegroundColor Yellow
Write-Host "   git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "   Note: You may need a Personal Access Token:" -ForegroundColor Yellow
Write-Host "   https://github.com/settings/tokens" -ForegroundColor White
Write-Host ""
Write-Host "3. Configure repository on GitHub:" -ForegroundColor Yellow
Write-Host "   - Add topics: ai, agents, mcp, ontology, self-healing, langchain, claude" -ForegroundColor White
Write-Host "   - Verify all files are present" -ForegroundColor White
Write-Host "   - Create a release (optional)" -ForegroundColor White
Write-Host ""
Write-Host "Your repository will be at:" -ForegroundColor Cyan
Write-Host "https://github.com/cloudbadal007/ontology-mcp-self-healing" -ForegroundColor Green
Write-Host ""
Write-Host "For detailed instructions, see: PUBLISH_TO_GITHUB.md" -ForegroundColor Yellow
Write-Host ""
