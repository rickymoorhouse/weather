FROM balenalib/armv7hf-alpine:3.11-run
LABEL io.balena.device-type="raspberrypi3"

RUN apk add --update \
		less \
		nano \
		net-tools \
		ifupdown \
		usbutils \
		gnupg \
		raspberrypi \
		raspberrypi-libs \
		raspberrypi-dev \
	&& rm -rf /var/cache/apk/*
RUN wind.py
