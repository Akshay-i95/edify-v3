# UI Testing Samples for Dynamic Follow-Up Detection

## Sample Test Scenario 1: Early Childhood Education Follow-Up

### Test Setup
- **URL**: `http://localhost:3000/?namespaces=kb-esp&role=teacher`
- **Namespace**: `kb-esp` (Early Childhood - Playgroup to IK3)
- **Role**: Teacher

### Test Steps

#### Step 1: Initial Query (New Thread)
```
What are effective assessment strategies for preschool children?
```
**Expected**: `is_follow_up: false` - New conversation thread

#### Step 2: Follow-Up Query 1
```
Can you give me specific examples?
```
**Expected**: `is_follow_up: true` - Dynamic detection should identify this as continuation

#### Step 3: Follow-Up Query 2 (Short phrase)
```
Tell me more
```
**Expected**: `is_follow_up: true` - Should detect very short follow-up

#### Step 4: Follow-Up Query 3 (Pronoun reference)
```
How do I implement these in my classroom?
```
**Expected**: `is_follow_up: true` - Should detect "these" as reference to previous content

#### Step 5: New Thread Test
Click "New Thread" button, then ask:
```
Hello
```
**Expected**: `is_follow_up: false` - Should reset to zero context and detect as casual conversation

---

## Sample Test Scenario 2: Middle School Mathematics Follow-Up

### Test Setup
- **URL**: `http://localhost:3000/?namespaces=kb-msp&role=teacher`
- **Namespace**: `kb-msp` (Middle School - Grades 6-10)
- **Role**: Teacher

### Test Steps

#### Step 1: Initial Query (New Thread)
```
What are the best practices for teaching algebra to Grade 6 students?
```
**Expected**: `is_follow_up: false` - New conversation thread

#### Step 2: Follow-Up Query 1 (Contextual)
```
What about differentiated instruction for struggling learners?
```
**Expected**: `is_follow_up: true` - Should detect topic continuation

#### Step 3: Follow-Up Query 2 (Elaboration request)
```
Can you elaborate on that?
```
**Expected**: `is_follow_up: true` - Should detect request for more detail

#### Step 4: Follow-Up Query 3 (Implementation focus)
```
How can I adapt this approach?
```
**Expected**: `is_follow_up: true` - Should detect "this approach" as reference

#### Step 5: New Thread Test
Click "New Thread" button, then ask:
```
What are assessment rubrics?
```
**Expected**: `is_follow_up: false` - Should start fresh conversation

---

## What to Look For During Testing

### ✅ Positive Indicators
- **Follow-up detection**: Look for `is_follow_up: true` in responses
- **Context continuity**: Responses should build on previous answers
- **Semantic understanding**: System should understand pronouns and references
- **Natural conversation flow**: No awkward topic jumps

### ❌ Negative Indicators to Watch
- **False positives**: New topics detected as follow-ups
- **False negatives**: Clear follow-ups detected as new queries
- **Context bleeding**: Previous conversation affecting new threads
- **Hardcoded pattern matching**: Responses that seem rule-based rather than semantic

### 🔍 Advanced Testing Tips

#### Test Dynamic Thresholds
Try these follow-up variations:
- Very short: "More?"
- Medium: "What else should I know?"
- Long: "Can you provide additional strategies for implementing these assessment techniques in a diverse classroom setting?"

#### Test Pronoun Resolution
Use these pronoun patterns:
- "it" - "How do I use it effectively?"
- "this" - "Can you explain this further?"
- "they" - "When should they be implemented?"
- "these" - "Are these suitable for all age groups?"

#### Test Context Reset
- Start conversation → Ask follow-ups → Click "New Thread" → Verify clean slate
- Multiple new threads should each start with `is_follow_up: false`

### 📊 Expected Performance Metrics
- **Follow-up Detection Rate**: >90% accuracy for clear follow-ups
- **False Positive Rate**: <10% for genuinely new topics
- **Response Time**: <2 seconds per query
- **Context Reset**: 100% success rate on new threads

---

## Quick Copy-Paste URLs for Testing

### Early Childhood Test:
```
http://localhost:3000/?namespaces=kb-esp&role=teacher
```

### Middle School Test:
```
http://localhost:3000/?namespaces=kb-msp&role=teacher
```

### Primary School Test (Bonus):
```
http://localhost:3000/?namespaces=kb-psp&role=teacher
```

### High School Test (Bonus):
```
http://localhost:3000/?namespaces=kb-ssp&role=teacher
```

Start with these URLs and follow the test scenarios above to validate the dynamic follow-up detection system!