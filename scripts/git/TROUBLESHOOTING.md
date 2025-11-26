# Git Troubleshooting Guide

## Lỗi: "Updates were rejected because the remote contains work"

### Nguyên nhân
Remote repository đã có code mà local chưa có.

### Giải pháp

#### Option 1: Pull và push (Khuyến nghị)
```bash
./scripts/git/push.sh --pull [branch]
```

Hoặc thủ công:
```bash
git pull origin [branch]
# Resolve conflicts nếu có
git push origin [branch]
```

#### Option 2: Sync với remote
```bash
./scripts/git/push.sh --sync [branch]
```

Script sẽ tự động:
- Detect conflicts
- Pull và merge nếu cần
- Hoặc đưa ra options: merge, force push, cancel

#### Option 3: Force push (Cẩn thận!)
Chỉ dùng nếu chắc chắn muốn ghi đè remote:

```bash
git push -f origin [branch]
```

⚠️ **WARNING:** Force push sẽ xóa code trên remote!

## Lỗi: "Merge conflict"

### Giải pháp

1. **Xem conflicts:**
   ```bash
   git status
   ```

2. **Fix conflicts trong files:**
   - Tìm các markers: `<<<<<<<`, `=======`, `>>>>>>>`
   - Chọn code bạn muốn giữ
   - Xóa markers

3. **Commit sau khi fix:**
   ```bash
   git add .
   git commit -m "Resolve merge conflicts"
   ```

4. **Push:**
   ```bash
   git push origin [branch]
   ```

## Lỗi: "Branch not found"

### Giải pháp

```bash
# Fetch từ remote
git fetch origin

# Checkout remote branch
git checkout -b [branch] origin/[branch]
```

## Lỗi: "Remote branch does not exist"

### Giải pháp

```bash
# Push branch mới lên remote
git push -u origin [branch]
```

## Workflow khi remote có code

### Scenario 1: Remote có README, local có code mới

```bash
# 1. Pull remote changes
git pull origin master

# 2. Resolve conflicts nếu có
# (Git sẽ tự merge nếu không conflict)

# 3. Push
git push origin master
```

### Scenario 2: Remote và local đều có thay đổi

```bash
# Sử dụng sync script
./scripts/git/sync_with_remote.sh master

# Hoặc manual
git pull origin master
# Fix conflicts
git add .
git commit -m "Merge remote changes"
git push origin master
```

### Scenario 3: Muốn ghi đè remote (cẩn thận!)

```bash
# Chỉ dùng nếu chắc chắn
git push -f origin master
```

## Best Practices

1. **Luôn pull trước khi push:**
   ```bash
   git pull origin [branch]
   git push origin [branch]
   ```

2. **Sử dụng sync script:**
   ```bash
   ./scripts/git/pull_and_push.sh [branch]
   ```

3. **Kiểm tra status trước:**
   ```bash
   git status
   git fetch origin
   git log HEAD..origin/[branch]
   ```

4. **Tránh force push** trừ khi thực sự cần thiết

## Quick Commands

```bash
# Fetch (không merge)
git fetch origin

# Pull (fetch + merge)
git pull origin [branch]

# Push
git push origin [branch]

# Force push (cẩn thận!)
git push -f origin [branch]

# Xem differences
git log HEAD..origin/[branch]
git diff HEAD origin/[branch]
```

