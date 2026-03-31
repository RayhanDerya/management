from django.db import models

class Member(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Absensi(models.Model):
    STATUS_CHOICES = [
        ('Hadir', 'Hadir'),
        ('Izin', 'Izin'),
        ('Sakit', 'Sakit'),
        ('Alpha', 'Alpha'),
    ]
    date = models.DateField()
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.name} - {self.status}"

class UangKas(models.Model):
    TYPE_CHOICES = [
        ('masuk', 'Pemasukan'),
        ('keluar', 'Pengeluaran'),
    ]
    date = models.DateField()
    description = models.CharField(max_length=200) 
    member = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - {self.amount}"