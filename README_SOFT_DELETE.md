# Soft-Delete Propagation - Quick Guide

## 🚀 Quick Start

This implementation adds automatic soft-delete propagation from `agent_instances` to `history` collection.

### What's New?

When you delete an agent instance (soft-delete), all associated messages in the history are now automatically marked as deleted.

---

## 📁 Files Created/Modified

### Modified:
- ✅ `src/conductor-gateway/src/api/app.py` (lines 1476-1518)
  - Added propagation logic to `delete_agent_instance()` function

### Created:
- 📄 `test_soft_delete_propagation.py` - Test suite
- 📄 `create_mongodb_index.py` - Index creation script
- 📄 `IMPLEMENTATION_SOFT_DELETE.md` - Full documentation
- 📄 `requisitos_propagacao_soft_delete.md` - Requirements (original)

---

## 🔧 Setup (One-Time)

### 1. Create MongoDB Indexes

```bash
cd /mnt/ramdisk/primoia-main/conductor-community
python create_mongodb_index.py
```

This creates optimized indexes for better performance:
- `{instance_id: 1, isDeleted: 1}` - Main compound index
- `{deleted_at: 1}` - Sparse index for cleanup queries

---

## 🧪 Testing

### Run Automated Tests:

```bash
# 1. Start the backend server
cd src/conductor-gateway
uvicorn src.api.app:app --reload --port 8000

# 2. In another terminal, run tests
cd /mnt/ramdisk/primoia-main/conductor-community
python test_soft_delete_propagation.py
```

### Manual Test:

```bash
# 1. Create an instance
curl -X POST http://localhost:8000/api/agents/instances \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "test", "config": {}}'

# 2. Note the instance_id from response

# 3. Delete the instance
curl -X DELETE http://localhost:8000/api/agents/instances/{instance_id}

# 4. Check the response includes "history_messages_affected"
```

---

## 📊 API Changes

### Response Example:

**Before**:
```json
{
  "success": true,
  "message": "Instance soft deleted successfully",
  "instance_id": "abc-123",
  "deletion_type": "soft",
  "isDeleted": true
}
```

**After** (NEW field added):
```json
{
  "success": true,
  "message": "Instance soft deleted successfully",
  "instance_id": "abc-123",
  "deletion_type": "soft",
  "isDeleted": true,
  "history_messages_affected": 42  ⬅️ NEW
}
```

---

## ✅ Verification

After implementation, verify:

1. **Code changes applied**:
   ```bash
   cd src/conductor-gateway
   git diff src/api/app.py
   ```

2. **MongoDB indexes created**:
   ```javascript
   // In MongoDB shell
   use conductor
   db.history.getIndexes()
   ```

3. **Tests pass**:
   ```bash
   python test_soft_delete_propagation.py
   ```

---

## 📖 Full Documentation

For detailed information, see:
- **Implementation details**: `IMPLEMENTATION_SOFT_DELETE.md`
- **Requirements**: `requisitos_propagacao_soft_delete.md`

---

## 🔍 How It Works

```
┌─────────────────────────────────────────────────┐
│ DELETE /api/agents/instances/{id}              │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
       ┌─────────────────────┐
       │ Backend (app.py)    │
       └──────────┬──────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│ agent_instances  │  │ history          │
│ isDeleted=true   │  │ isDeleted=true   │
│ deleted_at=...   │  │ deleted_at=...   │
└──────────────────┘  └──────────────────┘
```

**Key Points**:
- ✅ Same timestamp for instance and messages
- ✅ Atomic operation (all or nothing)
- ✅ Returns count of affected messages
- ✅ Hard-delete behavior unchanged
- ✅ Backward compatible

---

## 🐛 Troubleshooting

### Test failing: "Cannot connect to server"
**Solution**: Start the backend server first
```bash
cd src/conductor-gateway
uvicorn src.api.app:app --reload --port 8000
```

### Index creation error
**Solution**: Check MongoDB connection
```bash
export MONGODB_URI="mongodb://localhost:27017"
export MONGODB_DB="conductor"
python create_mongodb_index.py
```

### No messages affected
**Possible reasons**:
- Instance has no messages (expected: `history_messages_affected: 0`)
- Instance already deleted (second delete returns 0)
- Wrong instance_id

---

## 🚀 Next Steps

After confirming everything works:

1. **Commit changes** (see git workflow below)
2. **Deploy to staging**
3. **Run tests in staging**
4. **Create indexes in production MongoDB**
5. **Deploy to production**
6. **Monitor logs** for confirmation

---

## 📝 Git Workflow

```bash
# 1. Commit in conductor-gateway submodule
cd src/conductor-gateway
git add src/api/app.py
git commit -m "feat(api): add soft-delete propagation to history collection"
git push origin HEAD

# 2. Commit in root monorepo
cd /mnt/ramdisk/primoia-main/conductor-community
git add src/conductor-gateway
git add test_soft_delete_propagation.py
git add create_mongodb_index.py
git add IMPLEMENTATION_SOFT_DELETE.md
git add README_SOFT_DELETE.md
git add requisitos_propagacao_soft_delete.md
git commit -m "feat(soft-delete): implement propagation to history collection

- Add automatic propagation of soft-delete to history messages
- Create test suite for all scenarios
- Add MongoDB index creation script
- Update documentation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin HEAD
```

---

**Status**: ✅ Implementation Complete
**Date**: 2025-11-02
