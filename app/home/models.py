from django.db import models


class User(models.Model):
	user_id = models.AutoField(primary_key=True, db_column='user_id')
	email_address = models.CharField(max_length=255)
	password = models.BinaryField()
	registered = models.BooleanField(default=False)
	registration_code = models.CharField(max_length=255)

	class Meta:
		db_table = 'users'
		managed = False


class Log(models.Model):
	log_id = models.AutoField(primary_key=True, db_column='log_id')
	time = models.DateTimeField()
	user_email = models.CharField(max_length=255)
	log_type = models.CharField(max_length=255)
	log_message = models.TextField()

	class Meta:
		db_table = 'logs'
		managed = False


class RainGauge(models.Model):
	id = models.AutoField(primary_key=True)
	location = models.CharField(max_length=255)
	latitude = models.FloatField()
	longitude = models.FloatField()

	class Meta:
		db_table = 'rainguage'
		managed = False


class Rainfall(models.Model):
	id = models.AutoField(primary_key=True)
	rainguage = models.ForeignKey(RainGauge, db_column='rainguage_id', on_delete=models.DO_NOTHING, related_name='rainfall_rows')
	rainfall = models.FloatField(db_column='rainfall')
	time = models.DateTimeField(null=True, blank=True)

	class Meta:
		db_table = 'rainfall'
		managed = False
