# Traçabilité : 2025-01-15-gift-card-checkout

Généré le : 2025-01-22T14:31:09Z

| AC      | Titre                          | Tests                                                                                                  | Code de production                                                              |
|---------|--------------------------------|--------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| AC-001  | Apply a valid gift card        | `giftcard.internal.DefaultGiftCardRedemptionServiceTest`, `giftcard.internal.GiftCardRedemptionIT`, `giftcard.internal.GiftCardControllerTest`, `giftcard.internal.GiftCardContractTest` | `giftcard.internal.DefaultGiftCardRedemptionService`, `giftcard.internal.GiftCardController` |
| AC-002  | Reject unknown card            | `giftcard.internal.DefaultGiftCardRedemptionServiceRejectionTest`, `giftcard.internal.GiftCardControllerTest`                                                                          | `giftcard.internal.DefaultGiftCardRedemptionService`                            |
| AC-003  | Reject expired card            | `giftcard.internal.DefaultGiftCardRedemptionServiceRejectionTest`, `giftcard.internal.GiftCardControllerTest`                                                                          | `giftcard.internal.DefaultGiftCardRedemptionService`                            |
| AC-004  | Reject depleted card           | `giftcard.internal.DefaultGiftCardRedemptionServiceRejectionTest`, `giftcard.internal.GiftCardControllerTest`                                                                          | `giftcard.internal.DefaultGiftCardRedemptionService`                            |
| AC-005  | Partial redemption             | `giftcard.internal.DefaultGiftCardRedemptionServiceTest`, `giftcard.internal.GiftCardRedemptionIT`                                                                                     | `giftcard.internal.DefaultGiftCardRedemptionService`, `giftcard.internal.GiftCardEntity` |
| AC-006  | Idempotent retry               | `giftcard.internal.IdempotentRedeemIT`, `giftcard.internal.GiftCardControllerTest`                                                                                                     | `giftcard.internal.IdempotencyStore`                                             |

## Notes

- Chaque AC possède au moins un test `@Tag("AC-NNN")`.
- La colonne du code est déduite des imports des tests et vérifiée manuellement pendant `$review`.
