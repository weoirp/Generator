// override macros that interfere with definitions.
#define DEPRECATED(...)
#define FORCEINLINE(...)

// use variants of macros defined in ObjectMacros.h that are meant to be active during edit.
#define UCLASS(...)
#define UINTERFACE(...)
#define UPROPERTY(...)
#define UFUNCTION(...)
#define USTRUCT(...)
#define UMETA(...)
#define UPARAM(...)
#define UENUM(...)
#define UDELEGATE(...)

#define GENERATED_BODY_LEGACY(...)
#define GENERATED_BODY(...)
#define GENERATED_USTRUCT_BODY(...)
#define GENERATED_UCLASS_BODY(...)
#define GENERATED_UINTERFACE_BODY(...)
#define GENERATED_IINTERFACE_BODY(...)
