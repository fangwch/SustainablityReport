FROM public.ecr.aws/lts/ubuntu:18.04

RUN apt-get update && apt-get install -y tzdata \
  && apt-get install -y --no-install-recommends libsndfile1 build-essential python3.6 python3.6-dev python3-pip \
  && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
  && dpkg-reconfigure --frontend noninteractive tzdata \
  && rm -rf /var/lib/apt/lists/* \
  && python3.6 -m pip install -U pip \
  && pip3 install wheel setuptools

WORKDIR /app

COPY ./requirements.txt .

ARG TZ=Asia/Shanghai

ENV LANG=C.UTF-8

RUN  pip3 install -r ./requirements.txt \
  && pip3 cache purge

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
