from rest_framework.viewsets import ModelViewSet
from chatbot.models import ConversationDetail
from chatbot.serializers import QuestionSerializer, ConversationSerializer
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from rest_framework import status,filters
from rest_framework.decorators import action
from chatbot.constants import Constant
from collections import Counter

def get_static_response():
        static_question = [
        "Bagaimana jika tanaman cabai yang baru ditanaman mengalami bercak bercak?",
        "Pada hari setelah tanam keberapa pupuk baiknya diberikan kepada padi?",
        "Perlukah tanaman cabai rawit dilakukan pruning?",
        "Bagaimana cara mengatasi ulat grayak pada daun bawang merah?",
        "Apa yang menyebabkan daun padi patah?"
        ]
        data = {
            'questions':static_question
        }
        return data

class QuestionViewSet(ModelViewSet):
    queryset = ConversationDetail.objects.all().order_by('-created_at')
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated] #Note: using custom SSOBearerAuthentication

    def list(self, request, *args, **kwargs):
        type = self.request.query_params.get('type')
        count = int(self.request.query_params.get('count')) if self.request.query_params.get('count') else 5

        question_types = ['recommended', 'frequent']
        if type not in question_types:
            return Response({"error": "Not a valid question type"}, status=status.HTTP_400_BAD_REQUEST)

        if type == 'recommended':
            return self.recommended_questions(count)
        else:
            return self.frequent_questions(count)

    #TODO:NLP integration pending
    def frequent_questions(self, count):
        data = get_static_response()
        # questions = ConversationDetail.objects.filter(role=Constant.USER).values_list('conversations', flat=True)
        # frequency_counter = Counter(questions)
        # top_elements = frequency_counter.most_common(count)
        # top_questions = []
        # for data, freq in top_elements:
        #     top_questions.append(data)
        # serializer = QuestionSerializer(data={'questions': top_questions})
        # serializer.is_valid(raise_exception=True)
        # return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(data, status=status.HTTP_200_OK)
    
    #TODO:NLP integration pending
    def recommended_questions(self, count):
        data = get_static_response()
        # questions = ConversationDetail.objects.filter(role=Constant.USER).values_list('conversations', flat=True)
        # frequency_counter = Counter(questions)
        # top_elements = frequency_counter.most_common(count)
        # top_questions = []
        # for data, freq in top_elements:
        #     top_questions.append(data)
        # serializer = QuestionSerializer(data={'questions': top_questions})
        # serializer.is_valid(raise_exception=True)
        # return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(data, status=status.HTTP_200_OK)


        

   
   
    

