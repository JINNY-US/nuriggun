import os
import requests
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status, permissions
from rest_framework.generics import get_object_or_404
from rest_framework import generics
from .models import Message
from .serializers import MessageDetailSerializer, MessageCreateSerializer

from .models import User,Report, EmailNotificationSettings
from article.models import Article, Comment

from user.serializers import (
    SubscribeSerializer,
    UserSerializer,
    UserCreateSerializer,
    Util,
    UserTokenObtainPairSerializer,
    PasswordResetSerializer,
    PasswordConfirmSerializer,
    KakaoLoginSerializer,
    HomeUserListSerializer,
    PasswordChangeSerializer,
    EmailNotificationSerializer,
)

# 이메일 인증 import
from base64 import urlsafe_b64encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import redirect
from django.utils.encoding import force_bytes

# 로그인 import
from rest_framework_simplejwt.views import TokenObtainPairView

# 소셜 로그인 import
from allauth.socialaccount.models import SocialAccount,SocialToken, SocialApp

# 비밀번호 재설정 import 
from django.utils.translation import gettext_lazy as _
from django.http import QueryDict

# HOME import
from rest_framework.pagination import LimitOffsetPagination
from django.db.models.functions import Random

# 메일보내기

from django.core.mail import EmailMessage
import threading
from django.conf import settings

class PasswordResetView(APIView):
        def post(self, request):
            '''비밀번호 재설정 이메일 전송'''
            serializer = PasswordResetSerializer(data=request.data)

            if serializer.is_valid():
                return Response({"message": "비밀번호 재설정 이메일 전송"}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordTokenCheckView(APIView):
    def get(self, request, uidb64, token):
        '''비밀번호 재설정 토큰 확인'''
        try:     
            user_id = urlsafe_base64_decode(uidb64).decode()
            print(user_id)

            user = get_object_or_404(User, id=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                return redirect("https://teamnuri.xyz/user/password_reset_failed.html")
            reset_url = f"https://teamnuri.xyz/user/password_reset_confirm.html?id={uidb64}&token={token}"
            return redirect(reset_url)

        except UnicodeDecodeError:
            return Response(
                {"message": "링크가 유효하지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED
            )

class PasswordResetConfirmView(APIView):
    def put(self, request):
        '''비밀번호 재설정 완료'''
        serializer = PasswordConfirmSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "비밀번호 재설정 완료"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication]

    def put(self, request, user_id):
        '''비밀번호 변경'''
        user = get_object_or_404(User, id=user_id)
        serializer = PasswordChangeSerializer(user, data=request.data, context={'user_id': user_id})
        if request.user == user:
            if serializer.is_valid():
                return Response({"message": "비밀번호 변경 완료"}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "수정권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

class SignUpView(APIView):
    def post(self, request):
        '''회원가입'''
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            user_id = urlsafe_b64encode(force_bytes(user.pk)).decode('utf-8')
            token = PasswordResetTokenGenerator().make_token(user)

            email = user.email
            auth_url = f"https://nuriggun.xyz/user/verify-email/{user_id}/{token}/"
            
            email_body = "이메일 인증" + auth_url
            message = {
                "subject": "[Nurriggun] 회원가입 인증 이메일입니다.",
                "message": email_body,
                "to_email": email,
            }
            Util.send_email(message)

            return Response({"message": "가입이 완료되었습니다."}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    def get(self, request, uidb64, token):
        '''이메일 인증'''
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        token_generator = PasswordResetTokenGenerator()

        if user is not None and token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return redirect("https://teamnuri.xyz/user/login.html")
        else:
            return redirect("https://teamnuri.xyz/user/password_reset_failed.html")

class LoginView(TokenObtainPairView):
    '''로그인'''
    serializer_class = UserTokenObtainPairSerializer

class UserView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication]

    def get(self, request, user_id):
        '''프로필 보기'''
        user = get_object_or_404(User, id=user_id)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def patch(self, request, user_id):
        '''프로필 수정하기'''
        user = get_object_or_404(User, id=user_id)
        if request.user == user:
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "수정권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)
        
    def delete(self,request, user_id):
        '''회원탈퇴 (계정 비활성화)'''
        user = get_object_or_404(User, id=user_id)
        if request.user == user:
            user.is_active = False
            user.save()
            return Response({"message": "탈퇴완료"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "탈퇴권한이 없습니다."}, status=status.HTTP_400_BAD_REQUEST) 

class SubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request, user_id):
        '''구독 등록/취소'''
        you = get_object_or_404(User, id=user_id)
        me = request.user
        if you != me:
            if me in you.subscribes.all():
                you.subscribes.remove(me)
                return Response("구독 취소", status=status.HTTP_205_RESET_CONTENT)
            else:
                you.subscribes.add(me)
                return Response("구독 완료", status=status.HTTP_200_OK)
        else:
            return Response("자신을 구독 할 수 없습니다.", status=status.HTTP_403_FORBIDDEN)

    def get(self, request, user_id):
        '''구독 리스트'''
        subscribes = User.objects.filter(id=user_id)
        subscribes_serializer = SubscribeSerializer(subscribes, many=True)
        return Response(
            {
                "subscribe": subscribes_serializer.data
            }
        )

# 쪽지 관련 view
class MessageInboxView(APIView):
    """ 받은 쪽지함 """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user
        messages = Message.objects.filter(receiver=user).order_by('-timestamp')
        received_messages_count = messages.count()
        unread_count = messages.filter(is_read=False).count()
        serializer = MessageDetailSerializer(messages, many=True)
        return Response(
            {"message_count": received_messages_count,
             "unread_count": unread_count,
             "messages": serializer.data},
            status=status.HTTP_200_OK)


class MessageSentView(APIView):
    """ 보낸 쪽지함 """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user
        messages = Message.objects.filter(sender=user)
        serializer = MessageDetailSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """ 쪽지 보내기(작성하기) """
        receiver_email = request.data.get('receiver')
        mutable_data = request.data.copy()
        mutable_data['receiver_email'] = receiver_email
        mutable_data_querydict = QueryDict(mutable_data.urlencode(), mutable=True)
        mutable_data_querydict.update(mutable_data)
        serializer = MessageCreateSerializer(data=mutable_data_querydict)

        if serializer.is_valid(raise_exception=True):
            serializer.save(sender=request.user)
            return Response(
                {"message": "쪽지를 보냈습니다.", "message_id": serializer.instance.id},
                status=status.HTTP_200_OK
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MessageDetailView(APIView):
    def get(self, request, message_id):
        """ 쪽지 상세보기 """
        message = get_object_or_404(Message, id=message_id)
        
        if request.user.is_authenticated:
            user = request.user.email
        else:
            user = None

        receiver = message.receiver.email

        if user == receiver and not message.is_read:
            message.is_read = True
            message.save()

        serializer = MessageDetailSerializer(message)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, message_id):
        """ 쪽지 삭제하기 """
        message = get_object_or_404(Message, id=message_id)
        message.delete()
        return Response({"message": "쪽지를 삭제했습니다."}, status=status.HTTP_204_NO_CONTENT)
    

class MessageReplyView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id):
        """ 쪽지 답장하기(작성하기) """

        receiver = request.data.get('receiver')
        mutable_data = request.data.copy()
        mutable_data['receiver_email'] = receiver
        mutable_data_querydict = QueryDict(mutable_data.urlencode(), mutable=True)
        mutable_data_querydict.update(mutable_data)
        serializer = MessageCreateSerializer(data=mutable_data_querydict)

        if serializer.is_valid(raise_exception=True):
            serializer.save(sender=request.user)
            reply_message = serializer.instance
            reply_message.reply_to = message_id
            reply_message.save()
            return Response(
                {"message": "쪽지를 보냈습니다.", "message_id": reply_message.id},
                status=status.HTTP_200_OK
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 소셜 로그인
class KakaoLoginView(APIView):
  def post(self, request):
    serializer = KakaoLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    code = serializer.validated_data["code"]

    # 인증 코드를 사용하여 액세스 토큰을 얻기 위해 카카오 서버에 요청
    access_token_response = requests.post(
      "https://kauth.kakao.com/oauth/token", 
      headers={"Content-Type": "application/x-www-form-urlencoded"},
      data={
        "grant_type": "authorization_code",
        "client_id": os.environ.get("KAKAO_REST_API_KEY"),
        "redirect_uri": "https://www.teamnuri.xyz/user/kakaocode.html", # 카카오에 등록된 리다이렉트 URI
        "code": code,
      },
    )

    # 액세스 토큰을 가져옴
    access_token_data = access_token_response.json()
    access_token = access_token_data.get("access_token")

    # 액세스 토큰을 사용하여 사용자 정보를 얻기 위해 카카오 서버에 요청
    user_info_response = requests.get( 
      "https://kapi.kakao.com/v2/user/me",
      headers={
        "Authorization": f"Bearer {access_token}",
        "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
      },
    )

    # 사용자 정보를 가져옴
    user_info_data = user_info_response.json()
    kakao_account = user_info_data.get("kakao_account")
    if kakao_account is not None:
      kakao_email = kakao_account.get("email")
    else:
      return Response({"error": "kakao_account 정보를 얻을 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
       
    properties = user_info_data.get("properties")
    if properties is not None:
      kakao_nickname = properties.get("nickname")
    else:
      return Response({"error": "properties 정보를 얻을 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

    kakao_id = user_info_data.get("id")

    try:
      # 사용자 이메일을 사용하여 유저 필터링
      user = User.objects.get(email=kakao_email)
      social_user = SocialAccount.objects.filter(user=user).first()

      # 유저가 존재하고 소셜 로그인 사용자인 경우
      if social_user:
        # 카카오가 아닌 경우 에러 메시지
        if social_user.provider != "kakao":
          return Response({"error": "카카오로 가입한 유저가 아닙니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 유저를 활성화하고 저장
        user.is_active = True
        user.save()

        # 토큰 생성 및 반환
        token_serializer = UserTokenObtainPairSerializer()
        tokens = token_serializer.for_user(user)
        return Response(tokens, status=status.HTTP_200_OK)

      # 유저가 존재하지만 소셜 로그인 사용자가 아닌 경우 에러 메시지
      if social_user is None:
        return Response({"error": "이메일이 존재하지만, 소셜 유저가 아닙니다."}, status=status.HTTP_400_BAD_REQUEST)

    # 유저가 존재하지 않는 경우
    except User.DoesNotExist:
      # 신규 유저를 생성하고 비밀번호를 설정하지 않음
      new_user = User.objects.create(nickname=kakao_nickname, email=kakao_email)
      new_user.set_unusable_password()
      new_user.is_active = True
      new_user.save()

      # 소셜 계정 생성
      new_social_account, created = SocialAccount.objects.get_or_create(provider="kakao", uid=kakao_id, user=new_user)
      if created:
        # allauth의 SocialApp
        social_app = SocialApp.objects.get(provider="kakao")

        # allauth의 SocialToken을 사용하여 토큰 생성
        SocialToken.objects.create(app=social_app, account=new_social_account, token=access_token)

      # 신규 유저 생성
      token_serializer = UserTokenObtainPairSerializer()
      tokens = token_serializer.for_user(new_user)
      return Response(tokens, status=status.HTTP_200_OK)
     
    return Response({"error": "알 수 없는 오류가 발생했습니다."}, status=status.HTTP_400_BAD_REQUEST)

# HOME
class HomeUserPagination(LimitOffsetPagination):
    default_limit = 12

class HomeUserListView(APIView):
    '''메인페이지 유저리스트 뷰'''
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = HomeUserPagination

    def get(self, request):
        users = User.objects.filter(is_active=True).order_by(Random())

        paginator = self.pagination_class()
        paginated_users = paginator.paginate_queryset(users, request)

        serializer = HomeUserListSerializer(paginated_users, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

# 신고 알림
class EmailThread(threading.Thread):
    def __init__(self, subject, message, to_email):
        self.subject = subject
        self.message = message
        self.to_email = to_email
        threading.Thread.__init__(self)

    def run(self):
        email = EmailMessage(
            subject=self.subject,
            body=self.message,
            to=[self.to_email],
            from_email=settings.DEFAULT_FROM_EMAIL,
        )
        email.send()

#신고
class ReportView(APIView):
    def post(self, request, user_id):
        reporter = request.user
        reported_user = get_object_or_404(User, id=user_id)

        if reporter == reported_user:
            return Response('자신을 신고할 수 없습니다.', status=status.HTTP_403_FORBIDDEN)

        # 한 번에 한 명의 유저만 신고 가능
        if Report.objects.filter(user=reporter, reported_user=reported_user).exists():
            return Response('이미 신고한 유저입니다.', status=status.HTTP_400_BAD_REQUEST)

        # Report 객체 생성
        report = Report(user=reporter, reported_user=reported_user,)
        report.save()

        # 신고된 유저의 신고 횟수 증가
        reported_user.report_count += 1
        reported_user.save()

        # k번 이상 신고된 유저인 경우 정지
        if reported_user.report_count >= 2:
            # 신고당한 유저 정지 처리
            reported_user.is_active = False
            reported_user.save()

            # 관련된 신고 내역 삭제
            Report.objects.filter(reported_user=reported_user).delete()
            Article.objects.filter(user=reported_user).delete()
            Comment.objects.filter(user=reported_user).delete()

            # 정지된 유저에게 메일 전송
            subject = "[Nurriggun] 계정 정지 안내"
            message = f"안녕하세요, {reported_user.nickname}님!\n\n계정이 정지되었습니다.\n문의 사항이 있으신 경우, 홈페이지의 '문의하기' 채팅을 이용해 주세요."
            to_email = reported_user.email

            email = EmailThread(subject, message, to_email)
            email.start()

            return Response('정지된 악질 유저입니다.', status=status.HTTP_200_OK)
        
        return Response('신고가 접수되었습니다.', status=status.HTTP_200_OK)
    
    
# 이메일 알림 동의
class EmailNotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        email_notification = EmailNotificationSettings.objects.filter(user=request.user)
        email_notification_serializer = EmailNotificationSerializer(email_notification, many=True)
        return Response(email_notification_serializer.data)

    def post(self, request):
        email_notification_settings = get_object_or_404(EmailNotificationSettings, user=request.user)
        email_notification_settings.email_notification = not email_notification_settings.email_notification
        email_notification_settings.save()

        if email_notification_settings.email_notification:
            return Response("이메일 알림에 동의하셨습니다", status=status.HTTP_200_OK)
        else:
            return Response("이메일 알림을 취소하셨습니다", status=status.HTTP_205_RESET_CONTENT)