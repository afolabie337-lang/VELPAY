from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .models import OTP


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {'user': UserSerializer(user).data, 'token': token.key},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'user': UserSerializer(user).data, 'token': token.key})


class ProfileView(RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user






class RequestOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.is_verified:
            return Response({'message': 'Account already verified.'})

        otp = OTP.generate_for_user(request.user)
        print(f"\n>>> OTP for {request.user.email}: {otp.code}\n")  # stand-in for SMS

        return Response({'message': 'OTP sent.'})


class VerifyOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code')

        otp = OTP.objects.filter(user=request.user, code=code, is_used=False).order_by('-created_at').first()

        if not otp:
            return Response({'error': 'Invalid code.'}, status=status.HTTP_400_BAD_REQUEST)
        if otp.is_expired():
            return Response({'error': 'Code has expired.'}, status=status.HTTP_400_BAD_REQUEST)

        otp.is_used = True
        otp.save()

        request.user.is_verified = True
        request.user.save()

        return Response({'message': 'Phone verified successfully.'})    