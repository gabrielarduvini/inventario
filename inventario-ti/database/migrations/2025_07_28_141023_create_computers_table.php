<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
   public function up(): void
{
    Schema::create('computers', function (Blueprint $table) {
        $table->id();
        $table->string('username');
        $table->string('hostname');
        $table->string('os');
        $table->string('ip_local');
        $table->string('ip_public')->nullable();
        $table->string('cpu');
        $table->string('ram');
        $table->string('disk');
        $table->timestamps();
    });
}


    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('computers');
    }
};
