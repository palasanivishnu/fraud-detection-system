from src.otp_service import generate_otp, verify_otp

user = "USER_001"

# Generate OTP
otp = generate_otp(user)

# Try correct OTP
print(verify_otp(user, otp))

# Try wrong OTP
print(verify_otp(user, "123456"))