# Matrice de traçabilité des exigences : <FEATURE-ID>

> Responsable : `spring-validator` · Phase 6 · Skill : `requirements-traceability`

## Matrix

| AC-ID | Tâches | Tests (statut) | Symboles de code | Portes exercées |
|---|---|---|---|---|
| AC-001 | T-001 | T-001-T1 ✅, T-001-T2 ✅ | `X#validate`, `X#apply` | unit, slice, IT, coverage |
| AC-002 | T-002 | T-002-T1 ✅, CONTRACT-001 ✅ | `Y#record`, `OrderReceipt#withRedemption` | unit, slice, contract |
| AC-003 | T-003 | T-003-T1 ✅ | `X#validate` | unit, slice |
| AC-004 | T-004 | T-004-T1 ✅, T-004-T2 ✅ | `X#guardOrderState` | unit, IT |
| AC-005 | T-005 | T-005-T1 ✅, PROP-001 ✅ | `X#applySequence` | unit, property |

## Coverage check

- AC sans test associé : **0** (doit valoir 0 pour être vert)
- Tests sans lien vers un AC : **0** (les tests orphelins deviennent des constats)
- Symboles de code modifiés dans le diff sans test associé : **0**

## Test → AC tagging convention

Les tests référencent un AC de l'une des deux manières suivantes :

```java
@Test
@DisplayName("AC-007: rejects expired card")
void rejectsExpiredCard() { ... }

// ou

@Test
@Tag("AC-007")
void rejectsExpiredCard() { ... }
```

Les deux formes sont reconnues par le validateur.

## Findings

- F-001 : <description>
