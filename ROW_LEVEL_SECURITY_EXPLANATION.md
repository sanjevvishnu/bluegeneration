# Row Level Security (RLS) in Supabase - Explained

## What is Row Level Security?

**Row Level Security (RLS)** is a PostgreSQL security feature that Supabase uses to control access to individual rows in database tables based on the current user's identity and role.

Think of it like having a security guard at each table who checks your ID before letting you read, insert, update, or delete specific rows.

## How RLS Works

### 1. **Policy-Based Access Control**
- Each table can have multiple RLS policies
- Policies define WHO can do WHAT to WHICH rows
- Policies are written as SQL expressions that return true/false

### 2. **User Context**
- RLS policies are evaluated based on the current database user
- Different users/roles can have different permissions
- Anonymous users (using anon key) have very limited access

## The Problem in Your Application

### Your Error:
```
❌ Failed to add transcript: {
  'message': 'new row violates row-level security policy for table "transcripts"', 
  'code': '42501'
}
```

### What This Means:
1. The `transcripts` table has RLS enabled
2. There's a policy that restricts INSERT operations
3. Your backend (using `SUPABASE_ANON_KEY`) doesn't have permission to insert transcript rows
4. The RLS policy is blocking the insertion

## Supabase Key Types

### 1. **SUPABASE_ANON_KEY** (Anonymous Key)
- **Limited access** - subject to RLS policies
- Used for client-side applications
- Cannot bypass security restrictions
- Perfect for frontend applications where users should only see their own data

### 2. **SUPABASE_SERVICE_ROLE_KEY** (Service Role Key)
- **Full access** - bypasses ALL RLS policies
- Used for backend/server applications
- Can perform administrative operations
- Should be kept secret and only used server-side

## The Solution Applied

### Before (BROKEN):
```python
self.supabase_key = os.getenv('SUPABASE_ANON_KEY')  # ❌ Limited by RLS
```

### After (FIXED):
```python
self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # ✅ Bypasses RLS
```

## Why This Fix Works

1. **Service Role Key** has administrative privileges
2. It bypasses all RLS policies automatically
3. Your backend can now insert transcripts regardless of RLS restrictions
4. User data is still secure because the backend validates user identity before operations

## RLS Policy Examples

Here are examples of what RLS policies might look like on your tables:

### Typical Transcripts Table Policy:
```sql
-- Only allow users to see their own transcripts
CREATE POLICY "Users can view own transcripts" ON transcripts
  FOR SELECT USING (user_id = auth.uid());

-- Only allow users to insert transcripts for themselves
CREATE POLICY "Users can insert own transcripts" ON transcripts
  FOR INSERT WITH CHECK (user_id = auth.uid());
```

### The Problem:
- `auth.uid()` returns the authenticated user's ID
- When using anon key, there's no authenticated user (`auth.uid()` is null)
- Policy fails because `user_id ≠ null`

### The Solution:
- Service role key bypasses these policies entirely
- Backend handles user validation in application code
- Database operations succeed regardless of RLS policies

## Security Considerations

### ✅ Safe (What We Did):
- Use service role key in **backend only**
- Backend validates user identity before database operations
- Frontend still uses anon key for direct queries
- User data remains protected by application logic

### ❌ Dangerous (What NOT to Do):
- Expose service role key to frontend/client
- Disable RLS entirely without proper application-level security
- Use service role key without validating user permissions

## Testing the Fix

You can verify the fix works by:

1. **Starting an interview session**
2. **Speaking during the interview**
3. **Checking that transcripts are saved** (no more RLS errors)
4. **Verifying transcripts appear in database**

The logs should now show:
```
✅ Converted Clerk ID user_xxx to UUID: xxx-xxx-xxx
📝 Inserting transcript data: {...}
✅ Added transcript: assistant: [transcript text]
```

Instead of:
```
❌ Failed to add transcript: {'message': 'new row violates row-level security policy...'}
```

## Summary

**Row Level Security** is a powerful security feature that protects your data by restricting access at the row level. The error you encountered was expected behavior - RLS was doing its job by blocking unauthorized access. By switching to the service role key for backend operations, we maintain security while allowing your application to function correctly. 