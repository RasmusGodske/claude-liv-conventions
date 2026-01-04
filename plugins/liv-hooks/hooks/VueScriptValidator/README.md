# VueScriptValidator

Ensures Vue single-file components use the Composition API with TypeScript.

## What It Does

When writing Vue files (`.vue`), this hook validates that the script tag uses:
- The `setup` attribute (Composition API)
- The `lang="ts"` attribute (TypeScript)

## Why

The project standardizes on:
- **Composition API** (`setup`) - Better TypeScript support, more explicit, easier to compose
- **TypeScript** (`lang="ts"`) - Type safety, better IDE support, catches errors early

## Examples

**Blocked:**
```vue
<script>
export default {
  data() { return { count: 0 } }
}
</script>
```

```vue
<script setup>
// Missing lang="ts"
</script>
```

```vue
<script lang="ts">
// Missing setup
</script>
```

**Allowed:**
```vue
<script setup lang="ts">
import { ref } from 'vue'
const count = ref(0)
</script>
```

```vue
<script lang="ts" setup>
// Order doesn't matter
</script>
```

## Performance

This hook uses fast regex matching (~milliseconds). No external calls.

## Configuration

Environment variables:
- `VUE_VALIDATOR_VERBOSE=1` - Enable verbose logging
- `VUE_VALIDATOR_LOG=/path/to/log` - Log to file
